import re
from typing import Any, Dict, List


def exact_match(predictions: List[Dict[str, Any]], key: str = "parsed_answer", ref_key: str = "reference_answer") -> Dict[str, Any]:
    """Compute exact-match accuracy.

    Args:
        predictions: List of prediction dicts, each must have `key` and the
                     original sample merged in (or `ref_key` available).
        key: Key for the predicted answer.
        ref_key: Key for the reference answer.

    Returns:
        Dict with accuracy, correct, total.
    """
    correct = 0
    total = 0
    details: List[Dict[str, Any]] = []
    for p in predictions:
        pred_ans = str(p.get(key, "")).strip()
        ref_ans = str(p.get(ref_key, "")).strip()
        match = pred_ans.lower() == ref_ans.lower()
        if match:
            correct += 1
        total += 1
        details.append({
            "sample_id": p.get("sample_id", ""),
            "predicted": pred_ans,
            "reference": ref_ans,
            "match": match,
        })

    accuracy = correct / total if total > 0 else 0.0
    return {
        "metric": "exact_match",
        "accuracy": round(accuracy, 4),
        "correct": correct,
        "total": total,
        "details": details,
    }


def contains_match(predictions: List[Dict[str, Any]], key: str = "parsed_answer", ref_key: str = "reference_answer") -> Dict[str, Any]:
    """Check if the reference answer is contained in the predicted answer."""
    correct = 0
    total = 0
    details: List[Dict[str, Any]] = []
    for p in predictions:
        pred_ans = str(p.get(key, "")).strip().lower()
        ref_ans = str(p.get(ref_key, "")).strip().lower()
        match = ref_ans in pred_ans if ref_ans else False
        if match:
            correct += 1
        total += 1
        details.append({
            "sample_id": p.get("sample_id", ""),
            "predicted": pred_ans,
            "reference": ref_ans,
            "match": match,
        })

    accuracy = correct / total if total > 0 else 0.0
    return {
        "metric": "contains_match",
        "accuracy": round(accuracy, 4),
        "correct": correct,
        "total": total,
        "details": details,
    }


def f1_score(predictions: List[Dict[str, Any]], key: str = "parsed_answer", ref_key: str = "reference_answer") -> Dict[str, Any]:
    """Compute token-level F1 score averaged over all predictions."""
    f1_scores: List[float] = []
    details: List[Dict[str, Any]] = []

    for p in predictions:
        pred_tokens = _tokenize(str(p.get(key, "")))
        ref_tokens = _tokenize(str(p.get(ref_key, "")))

        common = set(pred_tokens) & set(ref_tokens)
        if not common:
            f1 = 0.0
        else:
            precision = len(common) / len(pred_tokens) if pred_tokens else 0.0
            recall = len(common) / len(ref_tokens) if ref_tokens else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        f1_scores.append(f1)
        details.append({
            "sample_id": p.get("sample_id", ""),
            "f1": round(f1, 4),
        })

    avg_f1 = sum(f1_scores) / len(f1_scores) if f1_scores else 0.0
    return {
        "metric": "f1_score",
        "average_f1": round(avg_f1, 4),
        "total": len(predictions),
        "details": details,
    }


def _tokenize(text: str) -> List[str]:
    """Simple whitespace + punctuation tokenizer."""
    return re.findall(r"\w+", text.lower())
