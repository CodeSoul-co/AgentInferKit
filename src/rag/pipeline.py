from typing import Any, Dict, List, Optional

from loguru import logger

from src.config import DATA_PROCESSED_DIR
from src.rag.chunker import ChunkStrategy, chunk
from src.rag import embedder
from src.rag import milvus_store
from src.utils.file_io import write_jsonl


def build_index(
    records: List[Dict[str, Any]],
    kb_name: str,
    strategy: str = "by_topic",
    chunk_size: int = 256,
    embedder_name: Optional[str] = None,
    version: str = "v1",
    on_progress: Optional[Any] = None,
) -> Dict[str, Any]:
    """Build a complete RAG index: chunk -> embed -> insert into Milvus.

    Args:
        records: Raw QA sample dicts to index.
        kb_name: Knowledge base name.
        strategy: Chunk strategy name (by_topic, by_sentence, by_token, by_paragraph).
        chunk_size: Target chunk size.
        embedder_name: Embedding model name override.
        version: Version string for the collection.
        on_progress: Optional callback fn(stage, done, total) for progress reporting.

    Returns:
        A stats dict: {kb_name, collection, total_chunks, chunk_strategy, embedder}.
    """
    chunk_strategy = ChunkStrategy(strategy)

    # Stage 1: chunking
    logger.info(f"Chunking {len(records)} records with strategy={strategy}, chunk_size={chunk_size}")
    chunks = chunk(records, strategy=chunk_strategy, chunk_size=chunk_size)

    # Fill kb_name into each chunk
    for c in chunks:
        c["kb_name"] = kb_name

    if on_progress:
        on_progress("chunking", len(chunks), len(chunks))
    logger.info(f"Produced {len(chunks)} chunks")

    # Stage 2: embedding
    logger.info("Embedding chunks...")
    texts = [c["text"] for c in chunks]
    embeddings = embedder.embed(texts, model_name=embedder_name)
    dim = embeddings.shape[1]

    if on_progress:
        on_progress("embedding", len(texts), len(texts))
    logger.info(f"Embedded {len(texts)} chunks, dim={dim}")

    # Stage 3: indexing into Milvus
    logger.info("Creating Milvus collection and inserting...")
    collection_name = milvus_store.create_collection(kb_name, version, dim)
    inserted = milvus_store.insert(collection_name, chunks, embeddings)

    if on_progress:
        on_progress("indexing", inserted, inserted)

    # Write chunk JSONL to data/processed/knowledge_chunks/
    chunks_dir = DATA_PROCESSED_DIR / "knowledge_chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)
    chunks_path = chunks_dir / f"{kb_name}.jsonl"
    write_jsonl(str(chunks_path), chunks)
    logger.info(f"Wrote chunk file: {chunks_path}")

    stats = {
        "kb_name": kb_name,
        "collection": collection_name,
        "total_chunks": len(chunks),
        "chunk_strategy": strategy,
        "embedder": embedder_name or embedder._model_name,
    }
    logger.info(f"Index build complete: {stats}")
    return stats
