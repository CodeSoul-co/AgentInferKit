from typing import Any, Callable, Dict, List

from src.evaluators import text_metrics, choice_metrics, rag_metrics, efficiency


# Metric name -> callable mapping
_METRIC_MAP: Dict[str, Callable] = {
    "exact_match": text_metrics.exact_match,
    "contains_match": text_metrics.contains_match,
    "f1_score": text_metrics.f1_score,
    "choice_accuracy": choice_metrics.choice_accuracy,
    "confusion_matrix": choice_metrics.confusion_matrix,
    "retrieval_hit_rate": rag_metrics.retrieval_hit_rate,
    "context_relevance": rag_metrics.context_relevance,
    "latency_stats": efficiency.latency_stats,
    "token_stats": efficiency.token_stats,
    "cost_estimate": efficiency.cost_estimate,
}


def evaluate(
    metric_name: str,
    predictions: List[Dict[str, Any]],
    **kwargs: Any,
) -> Dict[str, Any]:
    """Run a single evaluation metric on predictions.

    Args:
        metric_name: Name of the metric (e.g. 'exact_match', 'choice_accuracy').
        predictions: List of prediction dicts.
        **kwargs: Extra keyword args forwarded to the metric function.

    Returns:
        The metric result dict.

    Raises:
        ValueError: If metric_name is unknown.
    """
    if metric_name not in _METRIC_MAP:
        available = ", ".join(sorted(_METRIC_MAP.keys()))
        raise ValueError(f"Unknown metric '{metric_name}'. Available: {available}")
    return _METRIC_MAP[metric_name](predictions, **kwargs)


def evaluate_all(
    predictions: List[Dict[str, Any]],
    metric_names: List[str],
    metric_kwargs: Dict[str, Dict[str, Any]] = None,
) -> Dict[str, Dict[str, Any]]:
    """Run multiple evaluation metrics and return all results.

    Args:
        predictions: List of prediction dicts.
        metric_names: List of metric names to compute.
        metric_kwargs: Optional per-metric keyword args.

    Returns:
        A dict mapping metric_name -> result dict.
    """
    metric_kwargs = metric_kwargs or {}
    results = {}
    for name in metric_names:
        kwargs = metric_kwargs.get(name, {})
        results[name] = evaluate(name, predictions, **kwargs)
    return results


def list_metrics() -> List[str]:
    """Return all available metric names."""
    return sorted(_METRIC_MAP.keys())
