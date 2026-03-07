from typing import Any, Dict, List


def latency_stats(predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute latency statistics across all predictions.

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
    """Compute token usage statistics across all predictions.

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


def cost_estimate(predictions: List[Dict[str, Any]], price_per_1k_prompt: float = 0.0, price_per_1k_completion: float = 0.0) -> Dict[str, Any]:
    """Estimate total API cost based on token usage and pricing.

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
