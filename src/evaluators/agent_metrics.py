"""Agent-specific evaluation metrics for tool-calling tasks."""

from typing import Any, Dict, List


def tool_selection_accuracy(predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Fraction of samples where predicted tool_id call sequence matches ground_truth.

    Compares tool_trace tool_ids against ground_truth.call_sequence tool_ids.
    """
    correct = 0
    total = 0
    for pred in predictions:
        gt = pred.get("ground_truth", {})
        gt_seq = gt.get("call_sequence", [])
        traces = pred.get("tool_trace", [])
        if not gt_seq:
            continue
        total += 1
        pred_ids = [t.get("tool_id", "") for t in traces]
        gt_ids = [c.get("tool_id", c) if isinstance(c, dict) else c for c in gt_seq]
        if pred_ids == gt_ids:
            correct += 1
    acc = correct / total if total else 0.0
    return {"metric": "tool_selection_accuracy", "accuracy": round(acc, 4), "correct": correct, "total": total}


def parameter_accuracy(predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Fraction of tool calls where parameters exactly match ground_truth."""
    correct = 0
    total = 0
    for pred in predictions:
        gt = pred.get("ground_truth", {})
        gt_seq = gt.get("call_sequence", [])
        traces = pred.get("tool_trace", [])
        for gt_call, trace in zip(gt_seq, traces):
            total += 1
            gt_params = gt_call.get("parameters", {}) if isinstance(gt_call, dict) else {}
            pred_params = trace.get("parameters", {})
            if gt_params == pred_params:
                correct += 1
    acc = correct / total if total else 0.0
    return {"metric": "parameter_accuracy", "accuracy": round(acc, 4), "correct": correct, "total": total}


def end_to_end_success_rate(predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Fraction of samples where parsed_answer matches ground_truth.final_answer."""
    correct = 0
    total = 0
    for pred in predictions:
        gt = pred.get("ground_truth", {})
        gt_answer = str(gt.get("final_answer", "")).strip().lower()
        parsed = str(pred.get("parsed_answer", "")).strip().lower()
        if not gt_answer:
            continue
        total += 1
        if parsed == gt_answer:
            correct += 1
    rate = correct / total if total else 0.0
    return {"metric": "end_to_end_success_rate", "rate": round(rate, 4), "correct": correct, "total": total}


def invalid_call_rate(predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Fraction of samples that called a tool outside available_tools."""
    invalid = 0
    total = 0
    for pred in predictions:
        available = set(pred.get("available_tools", []))
        traces = pred.get("tool_trace", [])
        if not available:
            continue
        total += 1
        for trace in traces:
            if trace.get("tool_id", "") not in available:
                invalid += 1
                break
    rate = invalid / total if total else 0.0
    return {"metric": "invalid_call_rate", "rate": round(rate, 4), "invalid": invalid, "total": total}


def avg_tool_calls(predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Average number of tool calls per sample."""
    counts = [len(pred.get("tool_trace", [])) for pred in predictions]
    avg = sum(counts) / len(counts) if counts else 0.0
    return {"metric": "avg_tool_calls", "avg": round(avg, 2), "total": len(counts)}


def avg_reasoning_steps(predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Average number of steps in reasoning_trace per sample."""
    step_counts = []
    for pred in predictions:
        trace = pred.get("reasoning_trace")
        if isinstance(trace, list):
            step_counts.append(len(trace))
        else:
            step_counts.append(0)
    avg = sum(step_counts) / len(step_counts) if step_counts else 0.0
    return {"metric": "avg_reasoning_steps", "avg": round(avg, 2), "total": len(step_counts)}
