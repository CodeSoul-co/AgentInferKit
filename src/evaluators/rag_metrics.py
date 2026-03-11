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
    Compute average retrieval score across all predictions.
    Higher scores indicate the retriever returns more semantically relevant chunks.
    
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


def retrieval_recall_at_k(
    predictions: List[Dict[str, Any]],
    ref_key: str = "reference_answer",
    top_k: int = 5,
) -> Dict[str, Any]:
    """
    Compute Retrieval Recall@K: fraction of golden evidence pieces found in top-k
    retrieved chunks, averaged over all samples.

    Uses text overlap to check whether the reference answer (or oracle chunk text)
    appears in the retrieved chunks.

    Args:
        predictions: List of prediction dicts with 'rag_context'.
        ref_key: Key for reference answer in the sample.
        top_k: Number of top retrieved chunks to consider.

    Returns:
        Dict with avg_recall, total, details.
    """
    recalls: List[float] = []
    details: List[Dict[str, Any]] = []

    for p in predictions:
        rag_ctx = p.get("rag_context", {})
        chunks = rag_ctx.get("retrieved_chunks", [])[:top_k]
        ref = str(p.get(ref_key, "")).strip().lower()

        if not ref or not chunks:
            recalls.append(0.0)
            details.append({
                "sample_id": p.get("sample_id", ""),
                "recall": 0.0,
                "num_chunks": len(chunks),
            })
            continue

        # Split reference into sentences for granular recall
        ref_sentences = [s.strip() for s in ref.replace("\n", ".").split(".") if s.strip()]
        if not ref_sentences:
            ref_sentences = [ref]

        chunk_text_combined = " ".join(c.get("text", "").lower() for c in chunks)
        found = sum(1 for s in ref_sentences if s.lower() in chunk_text_combined)
        recall = found / len(ref_sentences)

        recalls.append(recall)
        details.append({
            "sample_id": p.get("sample_id", ""),
            "recall": round(recall, 4),
            "found_sentences": found,
            "total_sentences": len(ref_sentences),
            "num_chunks": len(chunks),
        })

    avg_recall = sum(recalls) / len(recalls) if recalls else 0.0
    return {
        "metric": "retrieval_recall_at_k",
        "avg_recall": round(avg_recall, 4),
        "top_k": top_k,
        "total": len(predictions),
        "details": details,
    }


def answer_evidence_consistency(
    predictions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Compute answer-evidence consistency: whether the model's parsed answer
    is grounded in the retrieved evidence chunks.

    Uses token-level overlap between the parsed answer and the concatenated
    chunk texts. A high score means the answer is well-supported by evidence.

    Returns:
        Dict with avg_consistency, total, details.
    """
    scores: List[float] = []
    details: List[Dict[str, Any]] = []

    for p in predictions:
        answer = str(p.get("parsed_answer", "")).strip().lower()
        rag_ctx = p.get("rag_context", {})
        chunks = rag_ctx.get("retrieved_chunks", [])

        if not answer or not chunks:
            scores.append(0.0)
            details.append({
                "sample_id": p.get("sample_id", ""),
                "consistency": 0.0,
                "has_evidence": bool(chunks),
            })
            continue

        evidence_text = " ".join(c.get("text", "").lower() for c in chunks)
        answer_tokens = set(answer.split())
        evidence_tokens = set(evidence_text.split())

        if not answer_tokens:
            scores.append(0.0)
        else:
            overlap = len(answer_tokens & evidence_tokens) / len(answer_tokens)
            scores.append(overlap)

        details.append({
            "sample_id": p.get("sample_id", ""),
            "consistency": round(scores[-1], 4),
            "answer_token_count": len(answer_tokens),
            "overlap_count": len(answer_tokens & evidence_tokens),
        })

    avg = sum(scores) / len(scores) if scores else 0.0
    return {
        "metric": "answer_evidence_consistency",
        "avg_consistency": round(avg, 4),
        "total": len(predictions),
        "details": details,
    }


def hallucination_rate(
    predictions: List[Dict[str, Any]],
    ref_key: str = "reference_answer",
) -> Dict[str, Any]:
    """
    Estimate hallucination rate: fraction of answer content that is neither
    in the retrieved evidence nor in the reference answer.

    A sample is considered hallucinated if more than 50% of the answer tokens
    cannot be found in either evidence or the reference.

    Returns:
        Dict with hallucination_rate, total, hallucinated_count, details.
    """
    hallucinated = 0
    total = 0
    details: List[Dict[str, Any]] = []

    for p in predictions:
        answer = str(p.get("parsed_answer", "")).strip().lower()
        ref = str(p.get(ref_key, "")).strip().lower()
        rag_ctx = p.get("rag_context", {})
        chunks = rag_ctx.get("retrieved_chunks", [])

        if not answer:
            continue

        total += 1
        evidence_text = " ".join(c.get("text", "").lower() for c in chunks)
        grounded_text = evidence_text + " " + ref
        grounded_tokens = set(grounded_text.split())
        answer_tokens = set(answer.split())

        # Filter out common stop words to reduce noise
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "can", "shall",
            "to", "of", "in", "for", "on", "with", "at", "by", "from",
            "as", "into", "through", "during", "before", "after",
            "and", "but", "or", "nor", "not", "so", "yet",
            "it", "its", "this", "that", "these", "those",
            "的", "了", "是", "在", "有", "不", "人", "他", "上", "个",
            "们", "中", "来", "下", "大", "为", "和", "也", "就",
        }
        content_tokens = answer_tokens - stop_words
        if not content_tokens:
            details.append({
                "sample_id": p.get("sample_id", ""),
                "hallucinated": False,
                "ungrounded_ratio": 0.0,
            })
            continue

        ungrounded = content_tokens - grounded_tokens
        ratio = len(ungrounded) / len(content_tokens)
        is_hallucinated = ratio > 0.5

        if is_hallucinated:
            hallucinated += 1

        details.append({
            "sample_id": p.get("sample_id", ""),
            "hallucinated": is_hallucinated,
            "ungrounded_ratio": round(ratio, 4),
            "ungrounded_tokens": len(ungrounded),
            "content_tokens": len(content_tokens),
        })

    rate = hallucinated / total if total > 0 else 0.0
    return {
        "metric": "hallucination_rate",
        "hallucination_rate": round(rate, 4),
        "hallucinated_count": hallucinated,
        "total": total,
        "details": details,
    }
