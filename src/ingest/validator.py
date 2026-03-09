"""Dataset validation — checks required fields and types per task_type."""

from typing import Any, Dict, List, Optional


VALID_TASK_TYPES = {"qa", "text_exam", "image_mcq", "api_calling"}
VALID_SPLITS = {"train", "dev", "test"}
VALID_MODALITIES = {"text", "image", "text+image"}
VALID_DIFFICULTIES = {"easy", "medium", "hard"}
VALID_EVAL_TYPES = {"em_or_f1", "choice_accuracy", "function_calling"}

# Per-task required fields (beyond the universal base fields)
_TASK_REQUIRED: Dict[str, List[str]] = {
    "qa": ["question", "answer"],
    "text_exam": ["question", "options", "answer"],
    "image_mcq": ["question", "options", "answer", "image_path"],
    "api_calling": ["user_goal", "available_tools", "ground_truth"],
}

# Universal required fields
_BASE_REQUIRED = ["sample_id", "task_type"]


def validate_sample(sample: Dict[str, Any]) -> Dict[str, Any]:
    """Validate a single sample dict.

    Returns:
        {"valid": bool, "errors": [...], "warnings": [...]}
    """
    errors: List[str] = []
    warnings: List[str] = []

    # Check base required
    for field in _BASE_REQUIRED:
        if field not in sample or sample[field] is None or sample[field] == "":
            errors.append(f"Missing required field: {field}")

    task_type = sample.get("task_type", "")
    if task_type and task_type not in VALID_TASK_TYPES:
        errors.append(f"Invalid task_type: '{task_type}'. Must be one of {VALID_TASK_TYPES}")

    # Check task-specific required fields
    if task_type in _TASK_REQUIRED:
        for field in _TASK_REQUIRED[task_type]:
            if field not in sample or sample[field] is None:
                errors.append(f"Missing required field for {task_type}: {field}")

    # Check metadata
    if "metadata" not in sample or not isinstance(sample.get("metadata"), dict):
        errors.append("Missing or invalid 'metadata' field (must be a dict)")

    # Warnings for auto-fillable fields
    if "split" not in sample:
        warnings.append("Missing 'split', will auto-fill 'test'")
    elif sample["split"] not in VALID_SPLITS:
        errors.append(f"Invalid split: '{sample['split']}'. Must be one of {VALID_SPLITS}")

    if "source" not in sample:
        warnings.append("Missing 'source', will auto-fill 'unknown'")

    if "modality" not in sample:
        warnings.append("Missing 'modality', will auto-fill 'text'")
    elif sample.get("modality") and sample["modality"] not in VALID_MODALITIES:
        errors.append(f"Invalid modality: '{sample['modality']}'. Must be one of {VALID_MODALITIES}")

    if "version" not in sample:
        warnings.append("Missing 'version', will auto-fill '1.0.0'")

    if "difficulty" in sample and sample["difficulty"] not in VALID_DIFFICULTIES:
        errors.append(f"Invalid difficulty: '{sample['difficulty']}'. Must be one of {VALID_DIFFICULTIES}")

    # Validate options for exam types
    if task_type in ("text_exam", "image_mcq"):
        options = sample.get("options")
        if isinstance(options, dict):
            if not options:
                errors.append("'options' dict is empty")
        answer = sample.get("answer", "")
        if isinstance(answer, str) and answer and isinstance(options, dict):
            if answer not in options:
                warnings.append(f"answer '{answer}' not found in options keys: {list(options.keys())}")

    # Validate api_calling ground_truth structure
    if task_type == "api_calling":
        gt = sample.get("ground_truth", {})
        if isinstance(gt, dict):
            if "call_sequence" not in gt:
                errors.append("api_calling ground_truth missing 'call_sequence'")
            if "final_answer" not in gt:
                warnings.append("api_calling ground_truth missing 'final_answer'")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


def validate_dataset(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate an entire dataset.

    Returns:
        {
            "valid": bool,
            "total": int,
            "valid_count": int,
            "error_count": int,
            "errors": [{"sample_id": ..., "errors": [...]}],
            "warnings": [...],
        }
    """
    all_errors: List[Dict[str, Any]] = []
    all_warnings: List[str] = []
    valid_count = 0
    sample_ids = set()

    for i, record in enumerate(records):
        sid = record.get("sample_id", f"<index_{i}>")

        # Check duplicate sample_id
        if sid in sample_ids:
            all_errors.append({"sample_id": sid, "errors": [f"Duplicate sample_id: {sid}"]})
        else:
            sample_ids.add(sid)

        result = validate_sample(record)
        if result["valid"]:
            valid_count += 1
        else:
            all_errors.append({"sample_id": sid, "errors": result["errors"]})
        all_warnings.extend(
            f"[{sid}] {w}" for w in result["warnings"]
        )

    return {
        "valid": len(all_errors) == 0,
        "total": len(records),
        "valid_count": valid_count,
        "error_count": len(all_errors),
        "errors": all_errors,
        "warnings": all_warnings,
    }
