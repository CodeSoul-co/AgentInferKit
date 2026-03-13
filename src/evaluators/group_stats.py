"""Group statistics — slice metrics by arbitrary metadata dimensions."""

from typing import Any, Callable, Dict, List, Optional


def _default_accuracy(items: List[Dict[str, Any]]) -> float:
    """Compute accuracy for a group of prediction+sample merged dicts."""
    if not items:
        return 0.0
    correct = 0
    for it in items:
        parsed = str(it.get("parsed_answer", "")).strip()
        ref = str(it.get("answer", it.get("reference_answer", ""))).strip()
        if not parsed or not ref:
            continue
        # Normalized string comparison
        if parsed.upper() == ref.upper():
            correct += 1
            continue
        # Numeric comparison fallback
        try:
            pred_val = float(parsed.replace(',', ''))
            gt_val = float(ref.replace(',', ''))
            if abs(pred_val - gt_val) < 1e-6:
                correct += 1
        except (ValueError, AttributeError):
            pass
    return round(correct / len(items), 4)


def _avg_field(items: List[Dict[str, Any]], path: str) -> float:
    """Compute average of a nested field (e.g. 'usage.total_tokens')."""
    vals = []
    for it in items:
        obj = it
        for key in path.split("."):
            if isinstance(obj, dict):
                obj = obj.get(key)
            else:
                obj = None
                break
        if obj is not None:
            try:
                vals.append(float(obj))
            except (ValueError, TypeError):
                pass
    return round(sum(vals) / len(vals), 2) if vals else 0.0


def group_stats(
    predictions: List[Dict[str, Any]],
    samples: List[Dict[str, Any]],
    group_field: str,
    metric_fn: Optional[Callable] = None,
) -> Dict[str, Dict[str, Any]]:
    """Compute per-group statistics.

    Args:
        predictions: List of prediction dicts.
        samples: List of original sample dicts (same order / matched by sample_id).
        group_field: Field to group by. Supports dot notation for metadata
                     subfields (e.g. 'metadata.topic', 'difficulty').
        metric_fn: Optional custom accuracy function. Defaults to exact-match accuracy.

    Returns:
        Dict mapping group_value -> {accuracy, count, avg_tokens, avg_latency_ms}
    """
    if metric_fn is None:
        metric_fn = _default_accuracy

    # Build sample lookup
    sample_map = {s.get("sample_id"): s for s in samples}

    # Merge sample fields into predictions for grouping
    merged: List[Dict[str, Any]] = []
    for pred in predictions:
        sid = pred.get("sample_id", "")
        item = dict(pred)
        if sid in sample_map:
            for k, v in sample_map[sid].items():
                item.setdefault(k, v)
        merged.append(item)

    # Group by field
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for item in merged:
        val = item
        for key in group_field.split("."):
            if isinstance(val, dict):
                val = val.get(key)
            else:
                val = None
                break
        group_key = str(val) if val is not None else "unknown"
        groups.setdefault(group_key, []).append(item)

    # Compute stats per group
    result = {}
    for gkey, items in sorted(groups.items()):
        result[gkey] = {
            "accuracy": metric_fn(items),
            "count": len(items),
            "avg_tokens": _avg_field(items, "usage.total_tokens"),
            "avg_latency_ms": _avg_field(items, "usage.latency_ms"),
        }

    return result


def multi_group_stats(
    predictions: List[Dict[str, Any]],
    samples: List[Dict[str, Any]],
    group_by: List[str],
    metric_fn: Optional[Callable] = None,
) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """Compute grouped statistics across multiple dimensions.

    Args:
        predictions: List of prediction dicts.
        samples: List of original sample dicts.
        group_by: List of field names to group by (e.g. ['difficulty', 'metadata.topic']).
        metric_fn: Optional custom accuracy function.

    Returns:
        Dict mapping "by_{dimension}" -> group_stats result.
    """
    result = {}
    for field in group_by:
        # Normalize key name: 'metadata.topic' -> 'by_topic', 'difficulty' -> 'by_difficulty'
        parts = field.split(".")
        dim_name = f"by_{parts[-1]}"
        result[dim_name] = group_stats(predictions, samples, field, metric_fn)
    return result
