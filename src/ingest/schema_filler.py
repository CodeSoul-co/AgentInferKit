"""Schema filler — auto-fill missing optional fields with sensible defaults."""

from typing import Any, Dict, List, Tuple


AUTO_FILL_DEFAULTS = {
    "split": "test",
    "difficulty": "medium",
    "version": "1.0.0",
    "modality": "text",
    "source": "unknown",
}

EVAL_TYPE_DEFAULTS = {
    "qa": "em_or_f1",
    "text_exam": "choice_accuracy",
    "image_mcq": "choice_accuracy",
    "api_calling": "function_calling",
}


def fill_defaults(sample: Dict[str, Any]) -> Dict[str, Any]:
    """Fill missing optional fields with defaults. Does not modify existing fields.

    Returns:
        A new dict with defaults filled in.
    """
    filled = dict(sample)

    for field, default in AUTO_FILL_DEFAULTS.items():
        if field not in filled or filled[field] is None or filled[field] == "":
            filled[field] = default

    # Auto-infer eval_type from task_type
    if "eval_type" not in filled or not filled["eval_type"]:
        task_type = filled.get("task_type", "")
        filled["eval_type"] = EVAL_TYPE_DEFAULTS.get(task_type, "em_or_f1")

    # Ensure metadata exists as dict
    if "metadata" not in filled or not isinstance(filled.get("metadata"), dict):
        filled["metadata"] = {}

    return filled


def fill_dataset(records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Fill defaults for an entire dataset.

    Returns:
        (filled_records, warnings) where warnings list fields that were auto-filled.
    """
    filled_records = []
    warnings: List[str] = []
    auto_filled_fields: Dict[str, int] = {}

    for record in records:
        sid = record.get("sample_id", "?")
        original_keys = set(record.keys())
        filled = fill_defaults(record)
        new_keys = set(filled.keys()) - original_keys

        for key in new_keys:
            auto_filled_fields[key] = auto_filled_fields.get(key, 0) + 1

        filled_records.append(filled)

    for field, count in sorted(auto_filled_fields.items()):
        warnings.append(f"Auto-filled '{field}' for {count}/{len(records)} samples")

    return filled_records, warnings
