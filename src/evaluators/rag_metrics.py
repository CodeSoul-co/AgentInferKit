"""
RAG (Retrieval-Augmented Generation) evaluation metrics.

Implements:
- Hit Rate: Whether golden context appears in Top-K retrieved chunks
- MRR (Mean Reciprocal Rank): Average of 1/rank for first relevant result

Input requirements:
- retrieved_ids: List of retrieved chunk IDs
- golden_context_ids: List of ground truth context IDs
"""

from typing import Any, Dict, List, Optional, Set

from .base import BaseEvaluator, EvaluationResult


class RAGEvaluator(BaseEvaluator):
    """
    Evaluator for RAG retrieval quality.
    
    Computes Hit Rate and MRR based on retrieved vs golden context IDs.
    """
    
    def __init__(self, top_k: int = 5, name: Optional[str] = None):
        """
        Initialize RAG evaluator.
        
        Args:
            top_k: Number of top retrieved results to consider
            name: Optional evaluator name
        """
        super().__init__(name=name)
        self.top_k = top_k
    
    def compute(
        self,
        predictions: List[str],
        references: List[str],
        retrieved_ids: Optional[List[List[str]]] = None,
        golden_context_ids: Optional[List[List[str]]] = None,
        **kwargs
    ) -> EvaluationResult:
        """
        Compute RAG retrieval metrics.
        
        Args:
            predictions: List of model predictions (not used directly, for interface compatibility)
            references: List of ground truth answers (not used directly)
            retrieved_ids: List of retrieved chunk ID lists per sample
            golden_context_ids: List of golden context ID lists per sample
            
        Returns:
            EvaluationResult with hit_rate and mrr metrics
        """
        if retrieved_ids is None or golden_context_ids is None:
            raise ValueError("retrieved_ids and golden_context_ids are required")
        
        if len(retrieved_ids) != len(golden_context_ids):
            raise ValueError(
                f"Length mismatch: {len(retrieved_ids)} retrieved vs {len(golden_context_ids)} golden"
            )
        
        n = len(retrieved_ids)
        if n == 0:
            return EvaluationResult(
                metrics={"hit_rate": 0.0, "mrr": 0.0},
                metadata={"top_k": self.top_k, "total": 0}
            )
        
        hits = 0
        reciprocal_ranks = []
        details = []
        
        for i, (retrieved, golden) in enumerate(zip(retrieved_ids, golden_context_ids)):
            golden_set: Set[str] = set(golden)
            top_k_retrieved = retrieved[:self.top_k]
            
            # Check hit (any golden in top-k)
            hit = any(rid in golden_set for rid in top_k_retrieved)
            if hit:
                hits += 1
            
            # Compute reciprocal rank (1/rank of first relevant result)
            rr = 0.0
            for rank, rid in enumerate(top_k_retrieved, start=1):
                if rid in golden_set:
                    rr = 1.0 / rank
                    break
            reciprocal_ranks.append(rr)
            
            details.append({
                "index": i,
                "hit": hit,
                "reciprocal_rank": round(rr, 4),
                "retrieved_count": len(top_k_retrieved),
                "golden_count": len(golden),
            })
        
        hit_rate = hits / n
        mrr = sum(reciprocal_ranks) / n
        
        return EvaluationResult(
            metrics={
                "hit_rate": round(hit_rate, 4),
                "mrr": round(mrr, 4),
            },
            details=details,
            metadata={
                "top_k": self.top_k,
                "total": n,
                "hits": hits,
            }
        )


def hit_rate(
    retrieved_ids: List[List[str]],
    golden_context_ids: List[List[str]],
    top_k: int = 5,
) -> float:
    """
    Compute Hit Rate: fraction of samples where at least one golden context
    appears in the top-k retrieved chunks.
    
    Args:
        retrieved_ids: List of retrieved chunk ID lists per sample
        golden_context_ids: List of golden context ID lists per sample
        top_k: Number of top results to consider
        
    Returns:
        Hit rate as a float between 0 and 1
    """
    if not retrieved_ids or not golden_context_ids:
        return 0.0
    
    hits = 0
    for retrieved, golden in zip(retrieved_ids, golden_context_ids):
        golden_set = set(golden)
        top_k_retrieved = retrieved[:top_k]
        if any(rid in golden_set for rid in top_k_retrieved):
            hits += 1
    
    return hits / len(retrieved_ids)


def mrr(
    retrieved_ids: List[List[str]],
    golden_context_ids: List[List[str]],
    top_k: int = 5,
) -> float:
    """
    Compute Mean Reciprocal Rank (MRR): average of 1/rank for the first
    relevant result in each sample's retrieved list.
    
    Args:
        retrieved_ids: List of retrieved chunk ID lists per sample
        golden_context_ids: List of golden context ID lists per sample
        top_k: Number of top results to consider
        
    Returns:
        MRR as a float between 0 and 1
    """
    if not retrieved_ids or not golden_context_ids:
        return 0.0
    
    reciprocal_ranks = []
    for retrieved, golden in zip(retrieved_ids, golden_context_ids):
        golden_set = set(golden)
        top_k_retrieved = retrieved[:top_k]
        
        rr = 0.0
        for rank, rid in enumerate(top_k_retrieved, start=1):
            if rid in golden_set:
                rr = 1.0 / rank
                break
        reciprocal_ranks.append(rr)
    
    return sum(reciprocal_ranks) / len(reciprocal_ranks)


def retrieval_hit_rate(predictions: List[Dict[str, Any]], ref_key: str = "reference_answer") -> Dict[str, Any]:
    """
    Legacy function: Compute retrieval hit rate from prediction dicts.
    
    Args:
        predictions: List of prediction dicts with 'rag_context' and ref_key
        
    Returns:
        Dict with hit_rate, hits, total, details
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

    hit_rate_val = hits / total if total > 0 else 0.0
    return {
        "metric": "retrieval_hit_rate",
        "hit_rate": round(hit_rate_val, 4),
        "hits": hits,
        "total": total,
        "details": details,
    }


def context_relevance(predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Legacy function: Compute average retrieval score across all predictions.
    
    Returns:
        Dict with avg_score, total, details
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
