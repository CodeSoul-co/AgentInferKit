"""
RAG (Retrieval-Augmented Generation) API routes.

Implements: knowledge base building, listing, search, and deletion.
Integrates with A组's RAG pipeline module.
"""

import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse

from .schemas import (
    ChunkResult,
    KnowledgeBaseInfo,
    KnowledgeBaseListResponse,
    RAGSearchRequest,
    RAGSearchResponse,
    ResponseEnvelope,
)


router = APIRouter(tags=["rag"])

# In-memory storage for knowledge bases (will be replaced by database in production)
_knowledge_bases: Dict[str, Dict[str, Any]] = {}

# Directory for RAG data
RAG_DATA_DIR = Path("data/rag")


def _get_kb_or_404(kb_name: str) -> Dict[str, Any]:
    """Get knowledge base by name or raise 404."""
    if kb_name not in _knowledge_bases:
        raise HTTPException(status_code=404, detail=f"Knowledge base '{kb_name}' not found")
    return _knowledge_bases[kb_name]


@router.post(
    "/build",
    summary="Build a knowledge base from uploaded file",
)
async def build_knowledge_base(
    file: UploadFile = File(..., description="JSONL file containing documents"),
    kb_name: str = Form(..., description="Knowledge base name"),
    chunk_strategy: str = Form("by_topic", description="Chunking strategy: by_topic, by_sentence, by_token"),
    chunk_size: int = Form(256, ge=64, le=2048, description="Chunk size in tokens"),
    embedder: str = Form("BAAI/bge-m3", description="Embedding model name"),
):
    """
    Build a knowledge base from uploaded documents.
    
    Returns an SSE stream for real-time progress updates during indexing.
    
    The file should be in JSONL format with each line containing:
    - text: Document text content
    - topic (optional): Topic label for the document
    - metadata (optional): Additional metadata
    """
    # Validate file type
    if not file.filename or not file.filename.endswith(".jsonl"):
        raise HTTPException(status_code=400, detail="File must be a JSONL file")
    
    # Check if KB already exists
    if kb_name in _knowledge_bases:
        raise HTTPException(status_code=409, detail=f"Knowledge base '{kb_name}' already exists")
    
    # Ensure RAG data directory exists
    RAG_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save uploaded file
    file_path = RAG_DATA_DIR / f"{kb_name}_source.jsonl"
    content = await file.read()
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Parse and validate JSONL
    lines = content.decode("utf-8").strip().split("\n")
    documents = []
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            doc = json.loads(line)
            if "text" not in doc:
                raise HTTPException(status_code=400, detail=f"Line {i+1}: missing 'text' field")
            documents.append(doc)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Line {i+1}: invalid JSON - {e}")
    
    if not documents:
        raise HTTPException(status_code=400, detail="File contains no valid documents")
    
    async def build_stream():
        """SSE stream for build progress."""
        try:
            total_docs = len(documents)
            collection_name = f"kb_{kb_name}_{uuid.uuid4().hex[:8]}"
            
            yield f"event: progress\ndata: {json.dumps({'stage': 'chunking', 'progress': 0, 'total': total_docs})}\n\n"
            
            # TODO: Integrate with A组's RAG pipeline
            # from src.rag.pipeline import RAGPipeline
            # pipeline = RAGPipeline(embedder=embedder)
            # chunks = pipeline.chunk_documents(documents, strategy=chunk_strategy, chunk_size=chunk_size)
            
            # Mock chunking progress
            chunks = []
            for i, doc in enumerate(documents):
                await asyncio.sleep(0.05)  # Simulate processing time
                
                # Simple mock chunking
                text = doc.get("text", "")
                chunk_id = f"chunk_{uuid.uuid4().hex[:8]}"
                chunks.append({
                    "chunk_id": chunk_id,
                    "text": text[:chunk_size] if len(text) > chunk_size else text,
                    "topic": doc.get("topic"),
                    "source_doc_idx": i,
                })
                
                if (i + 1) % 10 == 0 or i == total_docs - 1:
                    yield f"event: progress\ndata: {json.dumps({'stage': 'chunking', 'progress': i + 1, 'total': total_docs})}\n\n"
            
            yield f"event: progress\ndata: {json.dumps({'stage': 'embedding', 'progress': 0, 'total': len(chunks)})}\n\n"
            
            # TODO: Integrate with A组's embedder
            # embeddings = pipeline.embed_chunks(chunks)
            
            # Mock embedding progress
            for i in range(len(chunks)):
                await asyncio.sleep(0.02)
                if (i + 1) % 20 == 0 or i == len(chunks) - 1:
                    yield f"event: progress\ndata: {json.dumps({'stage': 'embedding', 'progress': i + 1, 'total': len(chunks)})}\n\n"
            
            yield f"event: progress\ndata: {json.dumps({'stage': 'indexing', 'progress': 0, 'total': len(chunks)})}\n\n"
            
            # TODO: Integrate with A组's Milvus store
            # from src.rag.milvus_store import MilvusStore
            # store = MilvusStore(collection_name=collection_name)
            # store.insert(chunks, embeddings)
            
            # Mock indexing progress
            for i in range(len(chunks)):
                await asyncio.sleep(0.01)
                if (i + 1) % 50 == 0 or i == len(chunks) - 1:
                    yield f"event: progress\ndata: {json.dumps({'stage': 'indexing', 'progress': i + 1, 'total': len(chunks)})}\n\n"
            
            # Store KB metadata
            _knowledge_bases[kb_name] = {
                "kb_name": kb_name,
                "total_chunks": len(chunks),
                "collection": collection_name,
                "embedder": embedder,
                "chunk_strategy": chunk_strategy,
                "chunk_size": chunk_size,
                "source_file": str(file_path),
                "created_at": datetime.now(),
            }
            
            yield f"event: done\ndata: {json.dumps({'kb_name': kb_name, 'total_chunks': len(chunks), 'collection': collection_name})}\n\n"
            
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"
    
    return StreamingResponse(
        build_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "",
    response_model=ResponseEnvelope[KnowledgeBaseListResponse],
    summary="List all knowledge bases",
)
async def list_knowledge_bases():
    """
    List all available knowledge bases.
    """
    kbs = [
        KnowledgeBaseInfo(
            kb_name=kb["kb_name"],
            total_chunks=kb["total_chunks"],
            collection=kb["collection"],
            embedder=kb["embedder"],
            created_at=kb["created_at"],
        )
        for kb in _knowledge_bases.values()
    ]
    
    # Sort by creation time (newest first)
    kbs.sort(key=lambda x: x.created_at, reverse=True)
    
    return ResponseEnvelope(
        data=KnowledgeBaseListResponse(kbs=kbs)
    )


@router.get(
    "/{kb_name}",
    response_model=ResponseEnvelope[KnowledgeBaseInfo],
    summary="Get knowledge base details",
)
async def get_knowledge_base(kb_name: str):
    """
    Get detailed information about a specific knowledge base.
    """
    kb = _get_kb_or_404(kb_name)
    
    return ResponseEnvelope(
        data=KnowledgeBaseInfo(
            kb_name=kb["kb_name"],
            total_chunks=kb["total_chunks"],
            collection=kb["collection"],
            embedder=kb["embedder"],
            created_at=kb["created_at"],
        )
    )


@router.post(
    "/search",
    response_model=ResponseEnvelope[RAGSearchResponse],
    summary="Search knowledge base",
)
async def search_knowledge_base(request: RAGSearchRequest):
    """
    Search a knowledge base for relevant chunks.
    
    Returns top-k most relevant chunks based on semantic similarity.
    """
    kb = _get_kb_or_404(request.kb_name)
    
    # TODO: Integrate with A组's retriever
    # from src.rag.retriever import Retriever
    # retriever = Retriever(collection_name=kb["collection"], embedder=kb["embedder"])
    # results = retriever.search(request.query, top_k=request.top_k)
    
    # Mock search results for demonstration
    mock_results = [
        ChunkResult(
            chunk_id=f"chunk_{i}",
            score=0.95 - i * 0.1,
            text=f"This is a mock search result {i+1} for query: {request.query[:50]}...",
            topic=f"topic_{i % 3}",
            source_qa_ids=[f"qa_{i}"],
        )
        for i in range(min(request.top_k, 5))
    ]
    
    return ResponseEnvelope(
        data=RAGSearchResponse(results=mock_results)
    )


@router.delete(
    "/{kb_name}",
    response_model=ResponseEnvelope[Dict[str, str]],
    summary="Delete a knowledge base",
)
async def delete_knowledge_base(kb_name: str):
    """
    Delete a knowledge base and its associated data.
    """
    kb = _get_kb_or_404(kb_name)
    
    # TODO: Integrate with A组's Milvus store to drop collection
    # from src.rag.milvus_store import MilvusStore
    # store = MilvusStore(collection_name=kb["collection"])
    # store.drop()
    
    # Delete source file if exists
    source_file = Path(kb.get("source_file", ""))
    if source_file.exists():
        source_file.unlink()
    
    # Remove from memory
    del _knowledge_bases[kb_name]
    
    return ResponseEnvelope(
        data={"deleted": kb_name}
    )
