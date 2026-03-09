"""
Efficiency evaluation metrics.

Implements:
- Tokens/sec: Token generation throughput
- Total Latency: End-to-end latency statistics
- Cost Estimation: API cost based on token usage and pricing

Input requirements:
- usage: Dict with prompt_tokens, completion_tokens, total_tokens
- duration: Request duration in seconds (or latency_ms in milliseconds)
"""

from typing import Any, Dict, List, Optional

from .base import BaseEvaluator, EvaluationResult


class EfficiencyEvaluator(BaseEvaluator):
    """
    Evaluator for inference efficiency metrics.
    
    Computes throughput, latency, and cost metrics.
    """
    
    def __init__(
        self,
        price_per_1k_prompt: float = 0.0,
        price_per_1k_completion: float = 0.0,
        name: Optional[str] = None,
    ):
        """
        Initialize efficiency evaluator.
        
        Args:
            price_per_1k_prompt: Cost per 1000 prompt tokens (USD)
            price_per_1k_completion: Cost per 1000 completion tokens (USD)
            name: Optional evaluator name
        """
        super().__init__(name=name)
        self.price_per_1k_prompt = price_per_1k_prompt
        self.price_per_1k_completion = price_per_1k_completion
    
    def compute(
        self,
        predictions: List[str],
        references: List[str],
        usage: Optional[List[Dict[str, Any]]] = None,
        duration: Optional[List[float]] = None,
        **kwargs
    ) -> EvaluationResult:
        """
        Compute efficiency metrics.
        
        Args:
            predictions: List of model predictions (for interface compatibility)
            references: List of ground truth answers (for interface compatibility)
            usage: List of usage dicts with prompt_tokens, completion_tokens, total_tokens
            duration: List of request durations in seconds
            
        Returns:
            EvaluationResult with tokens_per_sec, latency, and cost metrics
        """
        if usage is None:
            raise ValueError("usage is required (list of dicts with token counts)")
        
        n = len(usage)
        if n == 0:
            return EvaluationResult(
                metrics={
                    "tokens_per_sec": 0.0,
                    "avg_latency_ms": 0.0,
                    "total_cost_usd": 0.0,
                },
                metadata={"total": 0}
            )
        
        # Extract token counts
        prompt_tokens = []
        completion_tokens = []
        total_tokens = []
        latencies_ms = []
        tokens_per_sec_list = []
        details = []
        
        for i, u in enumerate(usage):
            pt = u.get("prompt_tokens", 0)
            ct = u.get("completion_tokens", 0)
            tt = u.get("total_tokens", pt + ct)
            prompt_tokens.append(pt)
            completion_tokens.append(ct)
            total_tokens.append(tt)
            
            # Get latency (prefer duration in seconds, fallback to latency_ms)
            lat_ms = 0.0
            if duration and i < len(duration):
                lat_ms = duration[i] * 1000  # Convert seconds to ms
            elif "latency_ms" in u:
                lat_ms = float(u["latency_ms"])
            elif "duration" in u:
                lat_ms = float(u["duration"]) * 1000
            latencies_ms.append(lat_ms)
            
            # Compute tokens/sec for this sample
            tps = 0.0
            if lat_ms > 0:
                tps = (ct / (lat_ms / 1000)) if ct > 0 else 0.0
            tokens_per_sec_list.append(tps)
            
            details.append({
                "index": i,
                "prompt_tokens": pt,
                "completion_tokens": ct,
                "total_tokens": tt,
                "latency_ms": round(lat_ms, 2),
                "tokens_per_sec": round(tps, 2),
            })
        
        # Aggregate metrics
        sum_prompt = sum(prompt_tokens)
        sum_completion = sum(completion_tokens)
        sum_total = sum(total_tokens)
        
        # Latency statistics
        sorted_latencies = sorted(latencies_ms)
        avg_latency = sum(latencies_ms) / n if n > 0 else 0.0
        p50_latency = sorted_latencies[n // 2] if n > 0 else 0.0
        p95_idx = min(int(n * 0.95), n - 1)
        p95_latency = sorted_latencies[p95_idx] if n > 0 else 0.0
        
        # Average tokens/sec
        avg_tps = sum(tokens_per_sec_list) / n if n > 0 else 0.0
        
        # Cost estimation
        cost = (
            (sum_prompt / 1000) * self.price_per_1k_prompt +
            (sum_completion / 1000) * self.price_per_1k_completion
        )
        
        return EvaluationResult(
            metrics={
                "tokens_per_sec": round(avg_tps, 2),
                "avg_latency_ms": round(avg_latency, 2),
                "p50_latency_ms": round(p50_latency, 2),
                "p95_latency_ms": round(p95_latency, 2),
                "total_cost_usd": round(cost, 6),
                "avg_prompt_tokens": round(sum_prompt / n, 1),
                "avg_completion_tokens": round(sum_completion / n, 1),
            },
            details=details,
            metadata={
                "total": n,
                "sum_prompt_tokens": sum_prompt,
                "sum_completion_tokens": sum_completion,
                "sum_total_tokens": sum_total,
                "price_per_1k_prompt": self.price_per_1k_prompt,
                "price_per_1k_completion": self.price_per_1k_completion,
            }
        )


def tokens_per_second(
    completion_tokens: List[int],
    duration_seconds: List[float],
) -> float:
    """
    Compute average tokens per second throughput.
    
    Args:
        completion_tokens: List of completion token counts per sample
        duration_seconds: List of generation durations in seconds
        
    Returns:
        Average tokens per second
    """
    if not completion_tokens or not duration_seconds:
        return 0.0
    
    total_tokens = sum(completion_tokens)
    total_duration = sum(duration_seconds)
    
    return total_tokens / total_duration if total_duration > 0 else 0.0


def latency_stats(predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Legacy function: Compute latency statistics across all predictions.

    Returns:
        Dict with avg_ms, p50_ms, p95_ms, min_ms, max_ms, total.
    """
    latencies = []
    for p in predictions:
        usage = p.get("usage", {})
        lat = usage.get("latency_ms")
        if lat is not None:
            latencies.append(float(lat))

    if not latencies:
        return {"metric": "latency_stats", "total": 0, "avg_ms": 0, "p50_ms": 0, "p95_ms": 0, "min_ms": 0, "max_ms": 0}

    latencies.sort()
    n = len(latencies)
    avg = sum(latencies) / n
    p50 = latencies[n // 2]
    p95_idx = min(int(n * 0.95), n - 1)
    p95 = latencies[p95_idx]

    return {
        "metric": "latency_stats",
        "total": n,
        "avg_ms": round(avg, 2),
        "p50_ms": round(p50, 2),
        "p95_ms": round(p95, 2),
        "min_ms": round(latencies[0], 2),
        "max_ms": round(latencies[-1], 2),
    }


def token_stats(predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Legacy function: Compute token usage statistics across all predictions.

    Returns:
        Dict with avg/total prompt_tokens, completion_tokens, total_tokens.
    """
    prompt_tokens: List[int] = []
    completion_tokens: List[int] = []
    total_tokens: List[int] = []

    for p in predictions:
        usage = p.get("usage", {})
        pt = usage.get("prompt_tokens", 0)
        ct = usage.get("completion_tokens", 0)
        tt = usage.get("total_tokens", pt + ct)
        prompt_tokens.append(pt)
        completion_tokens.append(ct)
        total_tokens.append(tt)

    n = len(predictions)
    if n == 0:
        return {"metric": "token_stats", "total": 0}

    return {
        "metric": "token_stats",
        "total": n,
        "sum_prompt_tokens": sum(prompt_tokens),
        "sum_completion_tokens": sum(completion_tokens),
        "sum_total_tokens": sum(total_tokens),
        "avg_prompt_tokens": round(sum(prompt_tokens) / n, 1),
        "avg_completion_tokens": round(sum(completion_tokens) / n, 1),
        "avg_total_tokens": round(sum(total_tokens) / n, 1),
    }


def cost_estimate(
    predictions: List[Dict[str, Any]],
    price_per_1k_prompt: float = 0.0,
    price_per_1k_completion: float = 0.0,
) -> Dict[str, Any]:
    """
    Legacy function: Estimate total API cost based on token usage and pricing.

    Args:
        predictions: List of prediction dicts with 'usage' field.
        price_per_1k_prompt: Cost per 1000 prompt tokens (USD).
        price_per_1k_completion: Cost per 1000 completion tokens (USD).

    Returns:
        Dict with estimated cost.
    """
    total_prompt = 0
    total_completion = 0
    for p in predictions:
        usage = p.get("usage", {})
        total_prompt += usage.get("prompt_tokens", 0)
        total_completion += usage.get("completion_tokens", 0)

    cost = (total_prompt / 1000) * price_per_1k_prompt + (total_completion / 1000) * price_per_1k_completion
    return {
        "metric": "cost_estimate",
        "total_prompt_tokens": total_prompt,
        "total_completion_tokens": total_completion,
        "price_per_1k_prompt": price_per_1k_prompt,
        "price_per_1k_completion": price_per_1k_completion,
        "estimated_cost_usd": round(cost, 6),
    }
