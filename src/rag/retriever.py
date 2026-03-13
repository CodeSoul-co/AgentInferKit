from typing import Any, Dict, List

from src.rag import embedder, milvus_store


def retrieve(
    query: str,
    kb_name: str,
    top_k: int = 5,
    collection_version: str = "v1",
    score_threshold: float = 0.0,
) -> List[Dict[str, Any]]:
    """Retrieve the most relevant chunks for a query from a knowledge base.

    Flow: embed(query) -> milvus search -> filter by score -> return chunks.

    Args:
        query: Natural language query string.
        kb_name: Knowledge base name.
        top_k: Number of chunks to retrieve.
        collection_version: Version suffix for the Milvus collection name.
        score_threshold: Minimum similarity score (0.0-1.0). Chunks below
                         this threshold are filtered out. Default 0.0 (no filtering).

    Returns:
        A list of dicts, each containing: chunk_id, text, topic, score.
    """
    collection_name = f"kb_{kb_name}_{collection_version}"
    query_vec = embedder.embed([query])[0]
    results = milvus_store.search(collection_name, query_vec, top_k=top_k)
    if score_threshold > 0:
        results = [r for r in results if r.get("score", 0) >= score_threshold]
    return results
