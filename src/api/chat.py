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


async def _mock_model_generate(
    messages: List[ChatMessage],
    model_id: str,
    strategy: str,
) -> Dict[str, Any]:
    """
    Mock model generation for development.
    
    In production, this will call the actual model adapter.
    """
    await asyncio.sleep(0.5)
    
    user_message = ""
    for msg in reversed(messages):
        if msg.role == "user":
            user_message = msg.content
            break
    
    if strategy == "cot":
        reasoning = f"Let me think about this step by step...\n1. First, I analyze the question: '{user_message[:50]}...'\n2. Then, I consider the relevant information.\n3. Finally, I formulate my answer."
        reply = f"Based on my analysis, here is my response to your question."
    elif strategy == "long_cot":
        reasoning = f"This requires deep thinking...\n\n## Step 1: Understanding\n{user_message[:100]}\n\n## Step 2: Analysis\nLet me break this down...\n\n## Step 3: Synthesis\nCombining all factors..."
        reply = "After careful consideration, here is my comprehensive answer."
    else:
        reasoning = None
        reply = f"Here is my response to: {user_message[:50]}..."
    
    return {
        "reply": reply,
        "reasoning_trace": reasoning,
        "usage": {
            "total_tokens": len(user_message.split()) * 2 + 100,
            "latency_ms": 500,
        }
    }


async def _mock_rag_retrieve(
    query: str,
    kb_name: str,
    top_k: int,
) -> List[ChunkResult]:
    """
    Mock RAG retrieval for development.
    
    In production, this will call the actual RAG retriever.
    """
    await asyncio.sleep(0.2)
    
    return [
        ChunkResult(
            chunk_id=f"chunk_{i:03d}",
            score=0.9 - i * 0.1,
            text=f"This is relevant context chunk {i + 1} for query: {query[:30]}...",
            topic="general",
            source_qa_ids=[f"qa_{i:03d}"],
        )
        for i in range(min(top_k, 3))
    ]


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
        
        chunks = await _mock_rag_retrieve(
            query=user_query,
            kb_name=request.rag.kb_name,
            top_k=request.rag.top_k,
        )
        rag_context = ChatRAGContext(retrieved_chunks=chunks)
    
    result = await _mock_model_generate(
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
            
            if request.strategy == "cot":
                response_text = f"Let me think step by step about: {user_query[:30]}... First, I'll analyze the question. Then, I'll consider the context. Finally, here is my answer."
            else:
                response_text = f"Here is my response to your question about: {user_query[:30]}..."
            
            tokens = response_text.split()
            total_tokens = len(tokens) + len(user_query.split())
            
            for token in tokens:
                yield f"event: token\ndata: {json.dumps({'token': token + ' '})}\n\n"
                await asyncio.sleep(0.05)
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            yield f"event: done\ndata: {json.dumps({'usage': {'total_tokens': total_tokens, 'latency_ms': latency_ms}})}\n\n"
            
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
