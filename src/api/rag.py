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
from loguru import logger

from .schemas import (
    ChunkResult,
    KnowledgeBaseInfo,
    KnowledgeBaseListResponse,
    RAGSearchRequest,
    RAGSearchResponse,
    ResponseEnvelope,
)


router = APIRouter(tags=["rag"])

# Directory for RAG data and KB state
RAG_DATA_DIR = Path("data/rag")
_KB_STATE_FILE = RAG_DATA_DIR / "_kb_state.json"


def _load_knowledge_bases() -> Dict[str, Dict[str, Any]]:
    """Load KB metadata from persistent JSON state file."""
    if not _KB_STATE_FILE.exists():
        return {}
    try:
        with open(_KB_STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        for kb in data.values():
            if isinstance(kb.get("created_at"), str):
                kb["created_at"] = datetime.fromisoformat(kb["created_at"])
        return data
    except (json.JSONDecodeError, OSError):
        return {}


def _save_knowledge_bases() -> None:
    """Persist KB metadata to JSON state file."""
    RAG_DATA_DIR.mkdir(parents=True, exist_ok=True)
    serialisable = {}
    for name, kb in _knowledge_bases.items():
        row = dict(kb)
        if isinstance(row.get("created_at"), datetime):
            row["created_at"] = row["created_at"].isoformat()
        serialisable[name] = row
    with open(_KB_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(serialisable, f, indent=2, ensure_ascii=False)


_knowledge_bases: Dict[str, Dict[str, Any]] = _load_knowledge_bases()


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
    chunk_overlap: int = Form(0, ge=0, le=512, description="Overlap between consecutive chunks"),
    embedder: str = Form("BAAI/bge-m3", description="Embedding model name"),
    force_rebuild: bool = Form(False, description="Force rebuild if KB already exists"),
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
    if kb_name in _knowledge_bases and not force_rebuild:
        raise HTTPException(status_code=409, detail=f"Knowledge base '{kb_name}' already exists. Use force_rebuild=true to overwrite.")
    
    # If force rebuild, clean up old data first
    if kb_name in _knowledge_bases and force_rebuild:
        old_kb = _knowledge_bases[kb_name]
        try:
            from src.rag.milvus_store import drop_collection
            drop_collection(old_kb["collection"])
        except Exception as e:
            logger.warning(f"Failed to drop old collection during rebuild: {e}")
        del _knowledge_bases[kb_name]
        _save_knowledge_bases()
    
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
        """SSE stream for build progress — delegates to src.rag.pipeline."""
        try:
            from src.rag.pipeline import build_index

            total_docs = len(documents)
            yield f"event: progress\ndata: {json.dumps({'stage': 'starting', 'progress': 0, 'total': total_docs})}\n\n"

            # build_index is synchronous; run in a thread to keep SSE alive
            loop = asyncio.get_event_loop()
            progress_events: List[Dict[str, Any]] = []

            def _on_progress(stage: str, done: int, total: int) -> None:
                progress_events.append({"stage": stage, "progress": done, "total": total})

            stats = await loop.run_in_executor(
                None,
                lambda: build_index(
                    records=documents,
                    kb_name=kb_name,
                    strategy=chunk_strategy,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    embedder_name=embedder if embedder != "BAAI/bge-m3" else None,
                    version="v1",
                    on_progress=_on_progress,
                ),
            )

            # Flush collected progress events
            for evt in progress_events:
                yield f"event: progress\ndata: {json.dumps(evt)}\n\n"

            collection_name = stats["collection"]

            # Store KB metadata and persist
            _knowledge_bases[kb_name] = {
                "kb_name": kb_name,
                "total_chunks": stats["total_chunks"],
                "collection": collection_name,
                "embedder": stats.get("embedder", embedder),
                "chunk_strategy": chunk_strategy,
                "chunk_size": chunk_size,
                "source_file": str(file_path),
                "created_at": datetime.now(),
            }
            _save_knowledge_bases()

            yield f"event: done\ndata: {json.dumps({'kb_name': kb_name, 'total_chunks': stats['total_chunks'], 'collection': collection_name})}\n\n"

        except Exception as e:
            logger.exception(f"RAG build failed for '{kb_name}'")
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

    try:
        from src.rag.retriever import retrieve
        # Extract kb_name and version from collection name (kb_{name}_{version})
        raw_results = retrieve(
            query=request.query,
            kb_name=request.kb_name,
            top_k=request.top_k,
        )
        results = [
            ChunkResult(
                chunk_id=r.get("chunk_id", ""),
                score=r.get("score", 0.0),
                text=r.get("text", ""),
                topic=r.get("topic"),
                source_qa_ids=r.get("source_qa_ids", []),
            )
            for r in raw_results
        ]
    except Exception as e:
        logger.warning(f"RAG search failed for '{request.kb_name}': {e}")
        results = []

    return ResponseEnvelope(
        data=RAGSearchResponse(results=results)
    )


@router.get(
    "/{kb_name}/chunks",
    summary="Export all chunks from a knowledge base",
)
async def export_chunks(kb_name: str):
    """
    Export all chunks from a knowledge base as a JSON list.
    Useful for evidence visualization and debugging.
    """
    kb = _get_kb_or_404(kb_name)
    
    # Read from the chunk JSONL file
    chunks_dir = Path("data/processed/knowledge_chunks")
    chunks_path = chunks_dir / f"{kb_name}.jsonl"
    
    if not chunks_path.exists():
        raise HTTPException(status_code=404, detail=f"Chunk file not found for '{kb_name}'")
    
    chunks = []
    with open(chunks_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                chunks.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    
    return ResponseEnvelope(
        data={
            "kb_name": kb_name,
            "total_chunks": len(chunks),
            "collection": kb.get("collection", ""),
            "chunk_strategy": kb.get("chunk_strategy", ""),
            "chunks": chunks,
        }
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

    # Drop Milvus collection
    try:
        from src.rag.milvus_store import drop_collection
        drop_collection(kb["collection"])
    except Exception as e:
        logger.warning(f"Failed to drop Milvus collection '{kb['collection']}': {e}")

    # Delete source file if exists
    source_file = Path(kb.get("source_file", ""))
    if source_file.exists():
        source_file.unlink()

    # Remove from memory and persist
    del _knowledge_bases[kb_name]
    _save_knowledge_bases()

    return ResponseEnvelope(
        data={"deleted": kb_name}
    )
