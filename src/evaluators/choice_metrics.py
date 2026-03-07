from typing import Any, Dict, List


def choice_accuracy(predictions: List[Dict[str, Any]], key: str = "parsed_answer", ref_key: str = "answer") -> Dict[str, Any]:
    """Compute accuracy for multiple-choice tasks (text_exam, image_mcq).

    Args:
        predictions: List of prediction dicts with `key` and `ref_key`.
        key: Key for the predicted choice letter.
        ref_key: Key for the correct answer letter.

    Returns:
        Dict with accuracy, correct, total, per_option_stats.
    """
    correct = 0
    total = 0
    option_stats: Dict[str, Dict[str, int]] = {}
    details: List[Dict[str, Any]] = []

    for p in predictions:
        pred_ans = str(p.get(key, "")).strip().upper()
        ref_ans = str(p.get(ref_key, "")).strip().upper()
        match = pred_ans == ref_ans
        if match:
            correct += 1
        total += 1

        # Track per-option accuracy
        if ref_ans not in option_stats:
            option_stats[ref_ans] = {"correct": 0, "total": 0}
        option_stats[ref_ans]["total"] += 1
        if match:
            option_stats[ref_ans]["correct"] += 1

        details.append({
            "sample_id": p.get("sample_id", ""),
            "predicted": pred_ans,
            "reference": ref_ans,
            "match": match,
        })

    accuracy = correct / total if total > 0 else 0.0

    per_option = {}
    for opt, stats in sorted(option_stats.items()):
        per_option[opt] = {
            "correct": stats["correct"],
            "total": stats["total"],
            "accuracy": round(stats["correct"] / stats["total"], 4) if stats["total"] > 0 else 0.0,
        }

    return {
        "metric": "choice_accuracy",
        "accuracy": round(accuracy, 4),
        "correct": correct,
        "total": total,
        "per_option": per_option,
        "details": details,
    }


def confusion_matrix(predictions: List[Dict[str, Any]], key: str = "parsed_answer", ref_key: str = "answer", labels: List[str] = None) -> Dict[str, Any]:
    """Build a confusion matrix for choice predictions.

    Args:
        predictions: List of prediction dicts.
        key: Predicted answer key.
        ref_key: Reference answer key.
        labels: List of option labels (default: A, B, C, D).

    Returns:
        Dict with the confusion matrix as a nested dict.
    """
    if labels is None:
        labels = ["A", "B", "C", "D"]

    matrix: Dict[str, Dict[str, int]] = {r: {p: 0 for p in labels} for r in labels}

    for pred in predictions:
        pred_ans = str(pred.get(key, "")).strip().upper()
        ref_ans = str(pred.get(ref_key, "")).strip().upper()
        if ref_ans in matrix and pred_ans in matrix[ref_ans]:
            matrix[ref_ans][pred_ans] += 1

    return {
        "metric": "confusion_matrix",
        "labels": labels,
        "matrix": matrix,
    }
