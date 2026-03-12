"""
Dataset management API routes.

Endpoints:
- POST /datasets/upload - Upload dataset file
- GET /datasets - List all datasets
- GET /datasets/{dataset_id}/preview - Preview dataset samples
- GET /datasets/{dataset_id}/stats - Get dataset statistics
- DELETE /datasets/{dataset_id} - Delete dataset
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile

from .schemas import (
    DatasetInfo,
    DatasetListResponse,
    DatasetStatsResponse,
    DatasetUploadResponse,
    ResponseEnvelope,
    SamplePreviewResponse,
)

router = APIRouter(tags=["datasets"])

DATA_DIR = Path("data/processed")
VALID_TASK_TYPES = {"qa", "text_exam", "image_mcq", "api_calling"}
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB


datasets_store: Dict[str, Dict[str, Any]] = {}

META_SUFFIX = ".meta.json"


def _save_meta(dataset_id: str, meta: Dict[str, Any]) -> None:
    """Persist dataset metadata to a JSON sidecar file."""
    file_path = Path(meta["file_path"])
    meta_path = file_path.with_suffix(".meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def _delete_meta(meta: Dict[str, Any]) -> None:
    """Delete the metadata sidecar file."""
    file_path = Path(meta["file_path"])
    meta_path = file_path.with_suffix(".meta.json")
    if meta_path.exists():
        meta_path.unlink()


def _scan_existing_datasets() -> None:
    """Scan data/processed/ and data/uploads/datasets/ on startup to rebuild datasets_store from disk."""
    scan_dirs = [DATA_DIR, Path("data/uploads/datasets")]
    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            continue
        for meta_path in scan_dir.rglob("*" + META_SUFFIX):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                dataset_id = meta.get("dataset_id")
                if dataset_id and dataset_id not in datasets_store:
                    # Verify the JSONL file still exists
                    if Path(meta["file_path"]).exists():
                        datasets_store[dataset_id] = meta
            except Exception:
                continue


# Rebuild store from disk on module load
_scan_existing_datasets()


def _load_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    """Load JSONL file and return list of records."""
    records = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def _validate_samples(samples: List[Dict[str, Any]], task_type: str) -> List[str]:
    """Validate samples and return warnings."""
    warnings = []
    # Task-specific required fields per ARCHITECTURE.md
    task_required = {
        "qa": ["question", "answer", "eval_type"],
        "text_exam": ["question", "options", "answer", "eval_type"],
        "image_mcq": ["question", "options", "answer"],
        "api_calling": ["user_goal", "available_tools", "ground_truth"],
    }
    # Auto-fill defaults per ARCHITECTURE.md schema_filler
    auto_fill_defaults = {
        "split": "test",
        "difficulty": "medium",
        "version": "1.0.0",
        "modality": "text",
    }
    eval_type_defaults = {
        "qa": "em_or_f1",
        "text_exam": "choice_accuracy",
        "image_mcq": "choice_accuracy",
        "api_calling": "function_calling",
    }
    
    fields = task_required.get(task_type, [])
    
    for i, sample in enumerate(samples):
        for field in fields:
            if field not in sample:
                warnings.append(f"第 {i + 1} 行缺少 {field} 字段")
        
        # Warn if image_mcq sample has no image reference at all
        if task_type == "image_mcq" and not sample.get("image_url") and not sample.get("image_path"):
            warnings.append(f"第 {i + 1} 行缺少 image_url 或 image_path 字段")
        
        # Auto-fill base fields
        if "sample_id" not in sample:
            sample["sample_id"] = f"s_{i + 1:05d}"
        if "task_type" not in sample:
            sample["task_type"] = task_type
        for key, default in auto_fill_defaults.items():
            if key not in sample:
                sample[key] = default
        if "eval_type" not in sample and task_type in eval_type_defaults:
            sample["eval_type"] = eval_type_defaults[task_type]
    
    return warnings


@router.post(
    "/upload",
    response_model=ResponseEnvelope[DatasetUploadResponse],
    summary="Upload dataset file",
)
async def upload_dataset(
    file: UploadFile = File(..., description="JSONL file, max 500MB"),
    dataset_name: str = Form(..., description="Dataset name (alphanumeric and underscore)"),
    task_type: str = Form(..., description="Task type: qa | text_exam | image_mcq | api_calling"),
    version: str = Form(default="1.0.0", description="Version number"),
    split: str = Form(default="test", description="Dataset split: train | dev | test"),
    description: str = Form(default="", description="Dataset description"),
) -> ResponseEnvelope[DatasetUploadResponse]:
    """
    Upload a dataset file in JSONL format.
    
    The file will be validated and stored in the processed data directory.
    """
    if task_type not in VALID_TASK_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid task_type. Must be one of: {VALID_TASK_TYPES}"
        )
    
    if not file.filename or not file.filename.endswith(".jsonl"):
        raise HTTPException(
            status_code=400,
            detail="File must be a .jsonl file"
        )
    
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    try:
        lines = content.decode("utf-8").strip().split("\n")
        samples = [json.loads(line) for line in lines if line.strip()]
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid JSONL format: {str(e)}"
        )
    
    warnings = _validate_samples(samples, task_type)
    
    dataset_id = f"{dataset_name}_v{version.replace('.', '_')}"
    
    if dataset_id in datasets_store:
        raise HTTPException(
            status_code=409,
            detail=f"Dataset '{dataset_id}' already exists. Please use a different name or version."
        )
    
    task_dir = DATA_DIR / task_type
    task_dir.mkdir(parents=True, exist_ok=True)
    file_path = task_dir / f"{dataset_id}.jsonl"
    
    with open(file_path, "w", encoding="utf-8") as f:
        for sample in samples:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")
    
    meta = {
        "dataset_id": dataset_id,
        "task_type": task_type,
        "total_samples": len(samples),
        "version": version,
        "split": split,
        "description": description,
        "file_path": str(file_path),
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    datasets_store[dataset_id] = meta
    _save_meta(dataset_id, meta)
    
    return ResponseEnvelope(
        code=0,
        message="ok",
        data=DatasetUploadResponse(
            dataset_id=dataset_id,
            file_path=str(file_path),
            total_samples=len(samples),
            validated=len(warnings) == 0,
            warnings=warnings[:10],  # Limit warnings
        )
    )


@router.get(
    "",
    response_model=ResponseEnvelope[DatasetListResponse],
    summary="List all datasets",
)
async def list_datasets(
    task_type: Optional[str] = Query(default=None, description="Filter by task type"),
) -> ResponseEnvelope[DatasetListResponse]:
    """
    List all available datasets, optionally filtered by task type.
    """
    datasets = []
    
    for ds_id, ds_info in datasets_store.items():
        if task_type and ds_info.get("task_type") != task_type:
            continue
        
        datasets.append(DatasetInfo(
            dataset_id=ds_info["dataset_id"],
            task_type=ds_info["task_type"],
            total_samples=ds_info["total_samples"],
            version=ds_info.get("version", "1.0.0"),
            created_at=datetime.fromisoformat(ds_info["created_at"].replace("Z", "+00:00")),
        ))
    
    return ResponseEnvelope(
        code=0,
        message="ok",
        data=DatasetListResponse(datasets=datasets)
    )


@router.get(
    "/{dataset_id}/preview",
    response_model=ResponseEnvelope[SamplePreviewResponse],
    summary="Preview dataset samples",
)
async def preview_dataset(
    dataset_id: str,
    offset: int = Query(default=0, ge=0, description="Offset"),
    limit: int = Query(default=10, ge=1, le=100, description="Number of samples to return"),
) -> ResponseEnvelope[SamplePreviewResponse]:
    """
    Preview samples from a dataset with pagination.
    """
    if dataset_id not in datasets_store:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
    
    ds_info = datasets_store[dataset_id]
    file_path = Path(ds_info["file_path"])
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Dataset file not found")
    
    samples = _load_jsonl(file_path)
    total = len(samples)
    
    paginated = samples[offset:offset + limit]
    
    return ResponseEnvelope(
        code=0,
        message="ok",
        data=SamplePreviewResponse(
            total=total,
            offset=offset,
            limit=limit,
            samples=paginated,
        )
    )


@router.get(
    "/{dataset_id}/stats",
    response_model=ResponseEnvelope[DatasetStatsResponse],
    summary="Get dataset statistics",
)
async def get_dataset_stats(
    dataset_id: str,
) -> ResponseEnvelope[DatasetStatsResponse]:
    """
    Get statistics for a dataset including distribution by split, difficulty, and topic.
    """
    if dataset_id not in datasets_store:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
    
    ds_info = datasets_store[dataset_id]
    file_path = Path(ds_info["file_path"])
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Dataset file not found")
    
    samples = _load_jsonl(file_path)
    
    by_split: Dict[str, int] = {}
    by_difficulty: Dict[str, int] = {}
    by_topic: Dict[str, int] = {}
    missing_fields: Dict[str, int] = {}
    
    check_fields = ["difficulty", "topic", "explanation", "split"]
    
    for sample in samples:
        split_val = sample.get("split", "unknown")
        by_split[split_val] = by_split.get(split_val, 0) + 1
        
        diff_val = sample.get("difficulty", "unknown")
        by_difficulty[diff_val] = by_difficulty.get(diff_val, 0) + 1
        
        topic_val = sample.get("topic")
        if topic_val:
            by_topic[topic_val] = by_topic.get(topic_val, 0) + 1
        
        for field in check_fields:
            if field not in sample:
                missing_fields[field] = missing_fields.get(field, 0) + 1
    
    return ResponseEnvelope(
        code=0,
        message="ok",
        data=DatasetStatsResponse(
            dataset_id=dataset_id,
            task_type=ds_info["task_type"],
            total=len(samples),
            by_split=by_split,
            by_difficulty=by_difficulty,
            by_topic=by_topic,
            missing_fields=missing_fields,
        )
    )


@router.delete(
    "/{dataset_id}",
    response_model=ResponseEnvelope[Dict[str, Any]],
    summary="Delete dataset",
)
async def delete_dataset(
    dataset_id: str,
) -> ResponseEnvelope[Dict[str, Any]]:
    """
    Delete a dataset and its associated file.
    """
    if dataset_id not in datasets_store:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
    
    ds_info = datasets_store[dataset_id]
    file_path = Path(ds_info["file_path"])
    
    _delete_meta(ds_info)
    if file_path.exists():
        file_path.unlink()
    
    del datasets_store[dataset_id]
    
    return ResponseEnvelope(
        code=0,
        message="ok",
        data={}
    )
