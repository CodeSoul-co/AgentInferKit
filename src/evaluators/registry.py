from collections import Counter
from typing import Any, Callable, Dict, List

from src.evaluators import text_metrics, choice_metrics, rag_metrics, efficiency
from src.evaluators import agent_metrics


# ---------------------------------------------------------------------------
# Wrapper functions: accept List[Dict] (our pipeline format) and delegate
# to friend B's evaluator functions which expect List[str] + List[str].
# ---------------------------------------------------------------------------

def _wrap_choice_accuracy(predictions: List[Dict[str, Any]], **kw) -> Dict[str, Any]:
    preds = [p.get("parsed_answer", "") for p in predictions]
    refs = [p.get("answer", p.get("reference_answer", "")) for p in predictions]
    acc = choice_metrics.choice_accuracy(preds, refs)
    correct = sum(1 for p, r in zip(preds, refs) if choice_metrics.extract_choice(p) == r.strip().upper())
    per_option: Dict[str, Dict[str, Any]] = {}
    for p, r in zip(preds, refs):
        r_norm = r.strip().upper()
        if r_norm not in per_option:
            per_option[r_norm] = {"correct": 0, "total": 0}
        per_option[r_norm]["total"] += 1
        if choice_metrics.extract_choice(p) == r_norm:
            per_option[r_norm]["correct"] += 1
    for v in per_option.values():
        v["accuracy"] = round(v["correct"] / v["total"], 4) if v["total"] else 0.0
    return {"metric": "choice_accuracy", "accuracy": acc, "correct": correct, "total": len(preds), "per_option": per_option}


def _wrap_exact_match(predictions: List[Dict[str, Any]], **kw) -> Dict[str, Any]:
    preds = [p.get("parsed_answer", "") for p in predictions]
    refs = [p.get("answer", p.get("reference_answer", "")) for p in predictions]
    matches = [text_metrics.exact_match(p, r) for p, r in zip(preds, refs)]
    return {"metric": "exact_match", "accuracy": sum(matches) / len(matches) if matches else 0.0, "total": len(matches)}


def _wrap_f1_score(predictions: List[Dict[str, Any]], **kw) -> Dict[str, Any]:
    preds = [p.get("parsed_answer", "") for p in predictions]
    refs = [p.get("answer", p.get("reference_answer", "")) for p in predictions]
    scores = [text_metrics.f1_score(p, r) for p, r in zip(preds, refs)]
    avg = sum(scores) / len(scores) if scores else 0.0
    return {"metric": "f1_score", "avg_f1": round(avg, 4), "total": len(scores)}


def _wrap_bleu(predictions: List[Dict[str, Any]], **kw) -> Dict[str, Any]:
    preds = [p.get("parsed_answer", "") for p in predictions]
    refs = [p.get("answer", p.get("reference_answer", "")) for p in predictions]
    scores = [text_metrics.bleu(p, r) for p, r in zip(preds, refs)]
    avg = sum(scores) / len(scores) if scores else 0.0
    return {"metric": "bleu", "avg_bleu": round(avg, 4), "total": len(scores)}


def _wrap_rouge_l(predictions: List[Dict[str, Any]], **kw) -> Dict[str, Any]:
    preds = [p.get("parsed_answer", "") for p in predictions]
    refs = [p.get("answer", p.get("reference_answer", "")) for p in predictions]
    scores = [text_metrics.rouge_l_f1(p, r) for p, r in zip(preds, refs)]
    avg = sum(scores) / len(scores) if scores else 0.0
    return {"metric": "rouge_l", "avg_rouge_l_f1": round(avg, 4), "total": len(scores)}


def _wrap_option_bias(predictions: List[Dict[str, Any]], **kw) -> Dict[str, Any]:
    preds = [p.get("parsed_answer", "") for p in predictions]
    counts: Counter = Counter()
    for p in preds:
        extracted = choice_metrics.extract_choice(p)
        counts[extracted or "INVALID"] += 1
    total = sum(counts.values())
    dist = {k: round(v / total, 4) for k, v in sorted(counts.items())} if total else {}
    return {"metric": "option_bias", "distribution": dist, "total": total}


def _wrap_win_rate(predictions: List[Dict[str, Any]], **kw) -> Dict[str, Any]:
    """Win rate: requires 'baseline_correct' field (bool) merged into predictions."""
    wins = 0
    comparable = 0
    for pred in predictions:
        baseline_correct = pred.get("baseline_correct")
        if baseline_correct is None:
            continue
        comparable += 1
        parsed = str(pred.get("parsed_answer", "")).strip().upper()
        ref = str(pred.get("answer", pred.get("reference_answer", ""))).strip().upper()
        target_correct = parsed == ref
        if target_correct and not baseline_correct:
            wins += 1
    rate = wins / comparable if comparable else 0.0
    return {"metric": "win_rate", "win_rate": round(rate, 4), "wins": wins, "comparable": comparable}


def _wrap_avg_trace_tokens(predictions: List[Dict[str, Any]], **kw) -> Dict[str, Any]:
    counts = []
    for pred in predictions:
        trace = pred.get("reasoning_trace")
        if isinstance(trace, str) and trace:
            counts.append(len(trace.split()))
        elif isinstance(trace, list) and trace:
            text = " ".join(str(s.get("thought", "")) for s in trace if isinstance(s, dict))
            counts.append(len(text.split()))
        else:
            counts.append(0)
    avg = sum(counts) / len(counts) if counts else 0.0
    return {"metric": "avg_trace_tokens", "avg": round(avg, 1), "total": len(counts)}


# Metric name -> callable mapping
_METRIC_MAP: Dict[str, Callable] = {
    # Text metrics
    "exact_match": _wrap_exact_match,
    "f1_score": _wrap_f1_score,
    "bleu": _wrap_bleu,
    "rouge_l": _wrap_rouge_l,
    # Choice metrics
    "choice_accuracy": _wrap_choice_accuracy,
    "option_bias": _wrap_option_bias,
    # Comparison metrics
    "win_rate": _wrap_win_rate,
    # RAG metrics
    "retrieval_hit_rate": rag_metrics.retrieval_hit_rate,
    "context_relevance": rag_metrics.context_relevance,
    # Efficiency metrics
    "latency_stats": efficiency.latency_stats,
    "token_stats": efficiency.token_stats,
    "cost_estimate": efficiency.cost_estimate,
    "avg_trace_tokens": _wrap_avg_trace_tokens,
    # Agent metrics
    "tool_selection_accuracy": agent_metrics.tool_selection_accuracy,
    "parameter_accuracy": agent_metrics.parameter_accuracy,
    "end_to_end_success_rate": agent_metrics.end_to_end_success_rate,
    "invalid_call_rate": agent_metrics.invalid_call_rate,
    "avg_tool_calls": agent_metrics.avg_tool_calls,
    "avg_reasoning_steps": agent_metrics.avg_reasoning_steps,
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
