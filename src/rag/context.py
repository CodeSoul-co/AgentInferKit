"""
RAG context injection helpers for runners.

Supports three modes:
- closed: No RAG, returns empty context.
- retrieved: Live retrieval from Milvus via embedder + vector search.
- oracle: Load pre-annotated ground-truth chunks from a JSONL file.
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from src.api.schemas import Message


def inject_rag_context(
    messages: List[Message],
    sample: Dict[str, Any],
    rag_config: Dict[str, Any],
) -> tuple:
    """Inject RAG context into messages and return (messages, rag_context_dict).

    Args:
        messages: Current message list (will be mutated if RAG is active).
        sample: The current sample dict.
        rag_config: RAG configuration dict with keys:
            enabled (bool), mode (str), kb_name (str), top_k (int),
            oracle_chunks_file (str, optional).

    Returns:
        A tuple of (messages, rag_context) where rag_context is a dict with:
            mode, query_text, retrieved_chunks, retrieval_latency_ms.
    """
    empty_context = {
        "mode": None,
        "query_text": None,
        "retrieved_chunks": [],
        "retrieval_latency_ms": 0,
    }

    if not rag_config.get("enabled"):
        return messages, empty_context

    mode = rag_config.get("mode", "retrieved")
    query = sample.get("question", "")

    if mode == "oracle":
        chunks, latency = _load_oracle_chunks(sample, rag_config)
    elif mode == "retrieved":
        chunks, latency = _retrieve_chunks(query, rag_config)
    else:
        return messages, empty_context

    rag_context = {
        "mode": mode,
        "query_text": query,
        "retrieved_chunks": [
            {
                "chunk_id": c.get("chunk_id", ""),
                "score": c.get("score", 1.0),
                "text": c.get("text", ""),
                "topic": c.get("topic", ""),
                "source_qa_ids": c.get("source_qa_ids", []),
            }
            for c in chunks
        ],
        "retrieval_latency_ms": latency,
    }

    # Inject context into the last user message
    if chunks:
        context_text = "\n\n".join(c.get("text", "") for c in chunks)
        if messages and messages[-1].role == "user":
            messages[-1] = Message(
                role="user",
                content=f"Reference:\n{context_text}\n\n{messages[-1].content}",
            )

    return messages, rag_context


def _retrieve_chunks(
    query: str, rag_config: Dict[str, Any]
) -> tuple:
    """Retrieve chunks from Milvus and return (chunks, latency_ms)."""
    from src.rag.retriever import retrieve as rag_retrieve

    kb_name = rag_config.get("kb_name", "")
    top_k = rag_config.get("top_k", 3)
    score_threshold = rag_config.get("score_threshold", 0.0)

    t0 = time.perf_counter()
    chunks = rag_retrieve(query, kb_name, top_k=top_k, score_threshold=score_threshold)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)

    return chunks, latency_ms


def _load_oracle_chunks(
    sample: Dict[str, Any], rag_config: Dict[str, Any]
) -> tuple:
    """Load ground-truth oracle chunks for a sample.

    Oracle chunks can come from:
    1. sample["oracle_chunks"] — directly embedded in the sample.
    2. A separate JSONL mapping file specified by rag_config["oracle_chunks_file"].
       Each line: {"sample_id": "...", "chunks": [...]}
    """
    t0 = time.perf_counter()

    # Source 1: inline oracle chunks
    if sample.get("oracle_chunks"):
        chunks = sample["oracle_chunks"]
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        return chunks, latency_ms

    # Source 2: external mapping file
    oracle_file = rag_config.get("oracle_chunks_file")
    if oracle_file:
        chunks = _lookup_oracle_file(oracle_file, sample.get("sample_id", ""))
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        return chunks, latency_ms

    logger.warning(
        f"Oracle mode requested but no oracle chunks found for sample "
        f"{sample.get('sample_id', '?')}"
    )
    return [], round((time.perf_counter() - t0) * 1000, 2)


# Simple file-level cache for oracle chunk files
_oracle_cache: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}


def _lookup_oracle_file(
    file_path: str, sample_id: str
) -> List[Dict[str, Any]]:
    """Look up oracle chunks from a JSONL mapping file (cached)."""
    if file_path not in _oracle_cache:
        mapping: Dict[str, List[Dict[str, Any]]] = {}
        path = Path(file_path)
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        sid = obj.get("sample_id", "")
                        mapping[sid] = obj.get("chunks", [])
                    except json.JSONDecodeError:
                        continue
        else:
            logger.warning(f"Oracle chunks file not found: {file_path}")
        _oracle_cache[file_path] = mapping

    return _oracle_cache.get(file_path, {}).get(sample_id, [])
