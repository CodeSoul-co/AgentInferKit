from typing import Any, Dict, List


def retrieval_hit_rate(predictions: List[Dict[str, Any]], ref_key: str = "reference_answer") -> Dict[str, Any]:
    """Compute retrieval hit rate: fraction of predictions where at least one
    retrieved chunk contains part of the reference answer.

    Args:
        predictions: List of prediction dicts, each with 'rag_context' and ref_key.

    Returns:
        Dict with hit_rate, hits, total.
    """
    hits = 0
    total = 0
    details: List[Dict[str, Any]] = []

    for p in predictions:
        rag_ctx = p.get("rag_context", {})
        chunks = rag_ctx.get("retrieved_chunks", [])
        ref = str(p.get(ref_key, "")).strip().lower()
        total += 1

        hit = False
        if ref and chunks:
            for c in chunks:
                chunk_text = str(c.get("text", "")).lower()
                if ref in chunk_text:
                    hit = True
                    break

        if hit:
            hits += 1
        details.append({
            "sample_id": p.get("sample_id", ""),
            "hit": hit,
            "num_chunks": len(chunks),
        })

    hit_rate = hits / total if total > 0 else 0.0
    return {
        "metric": "retrieval_hit_rate",
        "hit_rate": round(hit_rate, 4),
        "hits": hits,
        "total": total,
        "details": details,
    }


def context_relevance(predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute average retrieval score across all predictions.

    Uses the 'score' field from retrieved chunks as a proxy for relevance.

    Returns:
        Dict with avg_score, total.
    """
    all_scores: List[float] = []
    details: List[Dict[str, Any]] = []

    for p in predictions:
        rag_ctx = p.get("rag_context", {})
        chunks = rag_ctx.get("retrieved_chunks", [])
        scores = [c.get("score", 0.0) for c in chunks]
        avg = sum(scores) / len(scores) if scores else 0.0
        all_scores.append(avg)
        details.append({
            "sample_id": p.get("sample_id", ""),
            "avg_chunk_score": round(avg, 4),
            "num_chunks": len(chunks),
        })

    overall_avg = sum(all_scores) / len(all_scores) if all_scores else 0.0
    return {
        "metric": "context_relevance",
        "avg_score": round(overall_avg, 4),
        "total": len(predictions),
        "details": details,
    }
