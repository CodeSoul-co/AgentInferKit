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

router = APIRouter(tags=["chat"])


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
    - data: {"content": "..."} - Streamed content chunk
    - data: {"done": true, "usage": {...}} - Completion signal with usage stats
    - data: {"error": "..."} - Error message
    
    This is a Mock implementation for WebUI development.
    In production, this will stream tokens from the actual model adapter.
    """
    
    async def generate_stream():
        try:
            start_time = time.time()
            total_tokens = 0
            
            # Extract user query
            user_query = ""
            for msg in reversed(request.messages):
                if msg.role == "user":
                    user_query = msg.content
                    break
            
            # Generate mock response chunks based on strategy
            if request.strategy == "cot":
                chunks = [
                    "让我一步一步思考这个问题...\n\n",
                    f"**问题分析**: 您问的是关于「{user_query[:20]}...」\n\n",
                    "**第一步**: 首先，我需要理解问题的核心。",
                    "这涉及到几个关键概念。\n\n",
                    "**第二步**: 接下来，我会分析相关的上下文信息。",
                    "根据已知条件，我们可以推断出...\n\n",
                    "**第三步**: 综合以上分析，",
                    "我的结论是：这是一个很好的问题，",
                    "答案需要从多个角度来考虑。\n\n",
                    "**最终答案**: 基于以上推理，我认为...",
                ]
            elif request.strategy == "long_cot":
                chunks = [
                    "# 深度思考\n\n",
                    "这是一个需要仔细分析的问题。",
                    f"您提到了「{user_query[:15]}...」，",
                    "让我从多个维度来探讨。\n\n",
                    "## 背景分析\n",
                    "首先，我们需要了解问题的背景...\n\n",
                    "## 核心论点\n",
                    "其次，关键的论点包括以下几点...\n\n",
                    "## 结论\n",
                    "综上所述，我的回答是...",
                ]
            else:
                # Direct strategy - simple response
                chunks = [
                    f"您好！关于您的问题「{user_query[:20]}...」，",
                    "我来为您解答。\n\n",
                    "这是一个很有意思的问题。",
                    "根据我的理解，",
                    "答案是这样的：\n\n",
                    "首先，我们需要考虑...",
                    "其次，还要注意...",
                    "最后，总结一下...\n\n",
                    "希望这个回答对您有帮助！",
                ]
            
            # Stream each chunk with delay to simulate token generation
            for chunk in chunks:
                total_tokens += len(chunk)
                yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.15)  # 150ms delay between chunks
            
            # Send completion signal
            latency_ms = int((time.time() - start_time) * 1000)
            done_data = {
                "done": True,
                "usage": {
                    "total_tokens": total_tokens,
                    "latency_ms": latency_ms,
                },
            }
            yield f"data: {json.dumps(done_data, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
