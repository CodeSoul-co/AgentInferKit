"""
Chat and debugging API routes.

Endpoints:
- POST /chat/complete - Single sample chat completion
- POST /chat/stream - Streaming chat completion (SSE)
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from .schemas import (
    ChatCompleteRequest,
    ChatCompleteResponse,
    ChatMessage,
    ChatRAGConfig,
    ChatRAGContext,
    ChunkResult,
    ResponseEnvelope,
    UsageInfo,
)

router = APIRouter(prefix="/chat", tags=["chat"])


async def _real_model_generate(
    messages: List[ChatMessage],
    model_id: str,
    strategy: str,
) -> Dict[str, Any]:
    """
    Real model generation using adapter + strategy.
    """
    from src.adapters.registry import load_adapter
    from src.api.schemas import Message as InternalMessage
    from src.strategies.registry import load_strategy

    # Determine provider from model_id (e.g. "deepseek-chat" -> "deepseek")
    provider = model_id.split("-")[0] if "-" in model_id else model_id
    adapter = load_adapter({"provider": provider, "model": model_id})

    # Build a pseudo-sample from chat messages for strategy prompt building
    user_message = ""
    for msg in reversed(messages):
        if msg.role == "user":
            user_message = msg.content
            break

    # Use strategy to build prompt if applicable
    try:
        strat = load_strategy(strategy)
        sample = {"task_type": "text_qa", "question": user_message}
        built_msgs = strat.build_prompt(sample)
    except Exception:
        built_msgs = [InternalMessage(role=m.role, content=m.content) for m in messages]

    result = await adapter.generate(built_msgs)

    reasoning_trace = None
    reply = result.content
    if strategy in ("cot", "long_cot"):
        try:
            strat = load_strategy(strategy)
            parsed = strat.parse_output(result.content, {"task_type": "text_qa", "question": user_message})
            reasoning_trace = parsed.get("reasoning_trace")
            if parsed.get("parsed_answer"):
                reply = result.content
        except Exception:
            pass

    return {
        "reply": reply,
        "reasoning_trace": reasoning_trace,
        "usage": {
            "total_tokens": (result.prompt_tokens or 0) + (result.completion_tokens or 0),
            "latency_ms": int(result.latency_ms),
        }
    }


async def _rag_retrieve(
    query: str,
    kb_name: str,
    top_k: int,
) -> List[ChunkResult]:
    """
    RAG retrieval using the real retriever.
    Falls back to empty list if Milvus is unavailable.
    """
    try:
        from src.rag.retriever import retrieve
        results = retrieve(query, collection_name=kb_name, top_k=top_k)
        return [
            ChunkResult(
                chunk_id=r.get("chunk_id", f"chunk_{i:03d}"),
                score=r.get("score", 0.0),
                text=r.get("text", ""),
                topic=r.get("topic"),
                source_qa_ids=r.get("source_qa_ids", []),
            )
            for i, r in enumerate(results)
        ]
    except Exception:
        return []


@router.post(
    "/complete",
    response_model=ResponseEnvelope[ChatCompleteResponse],
    summary="Single sample chat completion",
)
async def chat_complete(
    request: ChatCompleteRequest,
) -> ResponseEnvelope[ChatCompleteResponse]:
    """
    Complete a chat conversation with optional RAG context.
    
    Supports different inference strategies (direct, cot, long_cot, tot).
    """
    start_time = time.time()
    
    rag_context = None
    if request.rag.enabled and request.rag.kb_name:
        user_query = ""
        for msg in reversed(request.messages):
            if msg.role == "user":
                user_query = msg.content
                break
        
        chunks = await _rag_retrieve(
            query=user_query,
            kb_name=request.rag.kb_name,
            top_k=request.rag.top_k,
        )
        rag_context = ChatRAGContext(retrieved_chunks=chunks)
    
    result = await _real_model_generate(
        messages=request.messages,
        model_id=request.model_id,
        strategy=request.strategy,
    )
    
    latency_ms = int((time.time() - start_time) * 1000)
    
    return ResponseEnvelope(
        code=0,
        message="ok",
        data=ChatCompleteResponse(
            reply=result["reply"],
            reasoning_trace=result.get("reasoning_trace"),
            rag_context=rag_context,
            usage=UsageInfo(
                total_tokens=result["usage"]["total_tokens"],
                latency_ms=latency_ms,
            ),
        )
    )


@router.post(
    "/stream",
    summary="Streaming chat completion (SSE)",
)
async def chat_stream(
    request: ChatCompleteRequest,
) -> StreamingResponse:
    """
    Stream chat completion tokens via Server-Sent Events.
    
    Events:
    - token: Individual token
    - done: Completion with usage stats
    - error: Error message
    """
    
    async def generate_stream():
        try:
            start_time = time.time()
            
            user_query = ""
            for msg in reversed(request.messages):
                if msg.role == "user":
                    user_query = msg.content
                    break
            
            result = await _real_model_generate(
                messages=request.messages,
                model_id=request.model_id,
                strategy=request.strategy,
            )

            reply = result["reply"]
            tokens = reply.split()

            for token in tokens:
                yield f"event: token\ndata: {json.dumps({'token': token + ' '})}\n\n"
                await asyncio.sleep(0.02)

            latency_ms = int((time.time() - start_time) * 1000)

            yield f"event: done\ndata: {json.dumps({'usage': {'total_tokens': result['usage']['total_tokens'], 'latency_ms': latency_ms}})}\n\n"
            
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
