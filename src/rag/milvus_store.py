from typing import Any, Dict, List, Optional

import numpy as np
from loguru import logger
from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    MilvusException,
    connections,
    utility,
)

from src.config import settings

_connected = False
_loaded_collections: set = set()


def _ensure_connection() -> None:
    """Ensure a connection to the Milvus server exists."""
    global _connected
    if _connected:
        return
    connections.connect(
        alias="default",
        host=settings.milvus_host,
        port=str(settings.milvus_port),
    )
    _connected = True
    logger.info(f"Connected to Milvus at {settings.milvus_host}:{settings.milvus_port}")


def create_collection(kb_name: str, version: str, dim: int, *, force: bool = False) -> str:
    """Create a Milvus collection for a knowledge base.

    Args:
        kb_name: Knowledge base name.
        version: Version string (e.g. 'v1').
        dim: Embedding vector dimension.
        force: If True, drop and recreate an existing collection.
               If False (default), return the existing collection name.

    Returns:
        The collection name string.
    """
    _ensure_connection()
    collection_name = f"kb_{kb_name}_{version}"

    if utility.has_collection(collection_name):
        if not force:
            logger.info(f"Collection '{collection_name}' already exists, reusing.")
            return collection_name
        logger.info(f"Collection '{collection_name}' already exists, dropping and recreating (force=True).")
        utility.drop_collection(collection_name)

    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="chunk_id", dtype=DataType.VARCHAR, max_length=128),
        FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
        FieldSchema(name="topic", dtype=DataType.VARCHAR, max_length=512),
        FieldSchema(name="source_qa_ids", dtype=DataType.VARCHAR, max_length=8192),
        FieldSchema(name="chunk_strategy", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="token_count", dtype=DataType.INT64),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),
    ]
    schema = CollectionSchema(fields=fields, description=f"RAG index for {kb_name}")
    collection = Collection(name=collection_name, schema=schema)

    # Create IVF_FLAT index on the embedding field
    index_params = {
        "metric_type": "IP",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 128},
    }
    collection.create_index(field_name="embedding", index_params=index_params)
    logger.info(f"Created collection '{collection_name}' with dim={dim}")
    return collection_name


def insert(
    collection_name: str,
    chunks: List[Dict[str, Any]],
    embeddings: np.ndarray,
) -> int:
    """Insert chunks and their embeddings into a Milvus collection.

    Args:
        collection_name: Target Milvus collection name.
        chunks: List of chunk dicts (must have 'chunk_id', 'text', 'topic').
        embeddings: Numpy array of shape (len(chunks), dim).

    Returns:
        Number of entities inserted.
    """
    _ensure_connection()
    collection = Collection(name=collection_name)

    import json as _json
    chunk_ids = [c["chunk_id"] for c in chunks]
    texts = [c["text"][:65535] for c in chunks]
    topics = [c.get("topic", "")[:512] for c in chunks]
    source_qa_ids = [_json.dumps(c.get("source_qa_ids", []))[:8192] for c in chunks]
    chunk_strategies = [c.get("chunk_strategy", "")[:64] for c in chunks]
    token_counts = [c.get("token_count", 0) for c in chunks]
    vectors = embeddings.tolist()

    data = [chunk_ids, texts, topics, source_qa_ids, chunk_strategies, token_counts, vectors]
    result = collection.insert(data)
    collection.flush()
    logger.info(f"Inserted {result.insert_count} entities into '{collection_name}'")
    return result.insert_count


def search(
    collection_name: str,
    query_embedding: np.ndarray,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """Search a Milvus collection for the nearest chunks.

    Args:
        collection_name: Collection to search.
        query_embedding: Query vector of shape (dim,).
        top_k: Number of results to return.

    Returns:
        A list of dicts with keys: chunk_id, text, topic, score.
    """
    _ensure_connection()
    collection = Collection(name=collection_name)
    if collection_name not in _loaded_collections:
        collection.load()
        _loaded_collections.add(collection_name)

    search_params = {"metric_type": "IP", "params": {"nprobe": 16}}
    results = collection.search(
        data=[query_embedding.tolist()],
        anns_field="embedding",
        param=search_params,
        limit=top_k,
        output_fields=["chunk_id", "text", "topic", "source_qa_ids", "chunk_strategy", "token_count"],
    )

    import json as _json
    hits = []
    for hit in results[0]:
        raw_ids = hit.entity.get("source_qa_ids", "[]")
        try:
            parsed_ids = _json.loads(raw_ids) if isinstance(raw_ids, str) else raw_ids
        except (ValueError, TypeError):
            parsed_ids = []
        hits.append({
            "chunk_id": hit.entity.get("chunk_id"),
            "text": hit.entity.get("text"),
            "topic": hit.entity.get("topic"),
            "source_qa_ids": parsed_ids,
            "chunk_strategy": hit.entity.get("chunk_strategy", ""),
            "token_count": hit.entity.get("token_count", 0),
            "score": float(hit.score),
        })
    return hits


def drop_collection(collection_name: str) -> None:
    """Drop a Milvus collection."""
    _ensure_connection()
    _loaded_collections.discard(collection_name)
    if utility.has_collection(collection_name):
        utility.drop_collection(collection_name)
        logger.info(f"Dropped collection '{collection_name}'")
    else:
        logger.warning(f"Collection '{collection_name}' does not exist, skipping drop.")
