"""
User uploads management API routes.

Supports local file import workflow: users clone the repo, drop their data
files into data/uploads/, and the system auto-discovers them for use in
experiments via the WebUI.

Endpoints:
- GET  /uploads/images       - List uploaded images
- GET  /uploads/images/{path} - Serve an uploaded image file
- GET  /uploads/datasets     - List locally-placed dataset files
- POST /uploads/scan         - Trigger re-scan of uploads directory
- POST /uploads/datasets/{filename}/register - Register a local JSONL as a dataset
"""

import json
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from loguru import logger

from .schemas import ResponseEnvelope

router = APIRouter(tags=["uploads"])

# Base directories
UPLOADS_DIR = Path("data/uploads")
UPLOADS_IMAGES_DIR = UPLOADS_DIR / "images"
UPLOADS_DATASETS_DIR = UPLOADS_DIR / "datasets"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg"}
DATASET_EXTENSIONS = {".jsonl"}

# Scheme prefix for local image references in JSONL files
UPLOADS_SCHEME = "uploads://"


def resolve_image_path(image_ref: str) -> Optional[str]:
    """Resolve an image reference to a usable URL or local path.

    Supports:
    - ``uploads://images/photo.jpg`` -> local file path
    - ``http://`` / ``https://`` -> returned as-is
    - Bare relative path ``images/photo.jpg`` -> resolved under uploads dir

    Returns:
        Absolute file path string for local files, or the original URL for
        remote references.  Returns None if the local file does not exist.
    """
    if image_ref.startswith(("http://", "https://")):
        return image_ref

    if image_ref.startswith(UPLOADS_SCHEME):
        rel = image_ref[len(UPLOADS_SCHEME):]
    else:
        rel = image_ref

    local_path = UPLOADS_DIR / rel
    if local_path.exists() and local_path.is_file():
        return str(local_path.resolve())
    return None


def get_image_serving_url(image_ref: str, base_url: str = "/api/v1/uploads") -> str:
    """Convert an image reference to an HTTP-servable URL.

    For remote URLs, returns as-is.  For local ``uploads://`` references,
    returns an API endpoint path that serves the file.

    The ``uploads://`` scheme is relative to ``data/uploads/``, so
    ``uploads://images/photo.jpg`` maps to the serve endpoint
    ``/api/v1/uploads/images/photo.jpg``.
    """
    if image_ref.startswith(("http://", "https://")):
        return image_ref

    if image_ref.startswith(UPLOADS_SCHEME):
        rel = image_ref[len(UPLOADS_SCHEME):]
    else:
        rel = image_ref

    # The serve endpoint is /images/{file_path} where file_path is relative
    # to data/uploads/images/.  Strip the leading "images/" from rel.
    if rel.startswith("images/"):
        file_path = rel[len("images/"):]
    else:
        file_path = rel

    return f"{base_url}/images/{file_path}"


# ---- Image endpoints ----

@router.get(
    "/images",
    response_model=ResponseEnvelope[Dict[str, Any]],
    summary="List uploaded images",
)
async def list_images(
    subdir: Optional[str] = Query(default=None, description="Subdirectory to list"),
):
    """
    List all image files in data/uploads/images/.

    Returns a flat list of relative paths suitable for use in dataset JSONL
    files as ``uploads://images/<path>``.
    """
    UPLOADS_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    target = UPLOADS_IMAGES_DIR
    if subdir:
        target = UPLOADS_IMAGES_DIR / subdir
        if not target.exists():
            raise HTTPException(status_code=404, detail=f"Subdirectory '{subdir}' not found")

    images = []
    for p in sorted(target.rglob("*")):
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS:
            rel = p.relative_to(UPLOADS_DIR)
            images.append({
                "filename": p.name,
                "path": str(rel),
                "ref": f"{UPLOADS_SCHEME}{rel}",
                "size_bytes": p.stat().st_size,
            })

    # List subdirectories
    subdirs = []
    for p in sorted(target.iterdir()):
        if p.is_dir() and p.name != "__pycache__":
            subdirs.append(p.name)

    return ResponseEnvelope(
        data={
            "total": len(images),
            "images": images,
            "subdirectories": subdirs,
            "base_ref": f"{UPLOADS_SCHEME}images/",
        }
    )


@router.get(
    "/images/{file_path:path}",
    summary="Serve an uploaded image",
)
async def serve_image(file_path: str):
    """
    Serve a specific image file from data/uploads/images/.

    This allows the WebUI to display local images without needing external URLs.
    """
    full_path = UPLOADS_IMAGES_DIR / file_path

    # Security: prevent directory traversal
    try:
        full_path = full_path.resolve()
        if not str(full_path).startswith(str(UPLOADS_IMAGES_DIR.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
    except Exception:
        raise HTTPException(status_code=403, detail="Invalid path")

    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail=f"Image not found: {file_path}")

    if full_path.suffix.lower() not in IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Not an image file")

    media_type = mimetypes.guess_type(str(full_path))[0] or "application/octet-stream"
    return FileResponse(full_path, media_type=media_type)


# ---- Dataset endpoints ----

@router.get(
    "/datasets",
    response_model=ResponseEnvelope[Dict[str, Any]],
    summary="List locally-placed dataset files",
)
async def list_upload_datasets():
    """
    List all JSONL files in data/uploads/datasets/ that users have placed
    locally after cloning the project.

    Files that are already registered in the dataset store are marked as such.
    """
    UPLOADS_DATASETS_DIR.mkdir(parents=True, exist_ok=True)

    from .datasets import datasets_store

    files = []
    for p in sorted(UPLOADS_DATASETS_DIR.rglob("*.jsonl")):
        if not p.is_file():
            continue
        rel = str(p.relative_to(UPLOADS_DATASETS_DIR))
        stem = p.stem

        # Check if already registered
        registered = any(
            Path(ds.get("file_path", "")).resolve() == p.resolve()
            for ds in datasets_store.values()
        )

        # Quick peek: count lines and detect task_type
        line_count = 0
        task_type = None
        try:
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    line_count += 1
                    if line_count == 1:
                        first = json.loads(line)
                        task_type = first.get("task_type")
        except Exception:
            pass

        files.append({
            "filename": p.name,
            "path": rel,
            "full_path": str(p),
            "size_bytes": p.stat().st_size,
            "sample_count": line_count,
            "task_type": task_type,
            "registered": registered,
        })

    return ResponseEnvelope(
        data={
            "total": len(files),
            "datasets": files,
        }
    )


@router.post(
    "/datasets/{filename}/register",
    response_model=ResponseEnvelope[Dict[str, Any]],
    summary="Register a local dataset file",
)
async def register_upload_dataset(
    filename: str,
    dataset_name: Optional[str] = Query(default=None, description="Override dataset name"),
    task_type: Optional[str] = Query(default=None, description="Override task type"),
    version: str = Query(default="1.0.0", description="Dataset version"),
):
    """
    Register a JSONL file from data/uploads/datasets/ as a usable dataset.

    The file is validated, auto-filled with missing fields, and added to the
    dataset store so it appears in the WebUI dataset selector.
    """
    file_path = UPLOADS_DATASETS_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")

    if not file_path.name.endswith(".jsonl"):
        raise HTTPException(status_code=400, detail="Only .jsonl files are supported")

    # Load and validate
    samples = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    samples.append(json.loads(line))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSONL: {e}")

    if not samples:
        raise HTTPException(status_code=400, detail="File contains no samples")

    # Infer task_type from first sample if not provided
    inferred_task = task_type or samples[0].get("task_type", "text_exam")
    name = dataset_name or file_path.stem
    dataset_id = f"{name}_v{version.replace('.', '_')}"

    from .datasets import datasets_store, _save_meta, _validate_samples

    if dataset_id in datasets_store:
        raise HTTPException(
            status_code=409,
            detail=f"Dataset '{dataset_id}' already registered. Use a different name or version."
        )

    # Validate and auto-fill
    warnings = _validate_samples(samples, inferred_task)

    # Write back the auto-filled version
    with open(file_path, "w", encoding="utf-8") as f:
        for sample in samples:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")

    meta = {
        "dataset_id": dataset_id,
        "task_type": inferred_task,
        "total_samples": len(samples),
        "version": version,
        "split": "test",
        "description": f"Imported from uploads/{filename}",
        "file_path": str(file_path),
        "source": "local_upload",
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    datasets_store[dataset_id] = meta
    _save_meta(dataset_id, meta)

    logger.info(f"Registered uploaded dataset: {dataset_id} ({len(samples)} samples)")

    return ResponseEnvelope(
        data={
            "dataset_id": dataset_id,
            "task_type": inferred_task,
            "total_samples": len(samples),
            "warnings": warnings[:10],
            "file_path": str(file_path),
        }
    )


@router.post(
    "/scan",
    response_model=ResponseEnvelope[Dict[str, Any]],
    summary="Rescan uploads directory",
)
async def scan_uploads():
    """
    Trigger a full rescan of the uploads directory.

    - Discovers new dataset files in data/uploads/datasets/
    - Counts available images in data/uploads/images/
    - Re-registers datasets that have .meta.json sidecar files
    """
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_DATASETS_DIR.mkdir(parents=True, exist_ok=True)

    # Count images
    image_count = sum(
        1 for p in UPLOADS_IMAGES_DIR.rglob("*")
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )

    # Scan datasets with existing .meta.json (auto-register)
    from .datasets import datasets_store, META_SUFFIX

    newly_registered = 0
    dataset_files = list(UPLOADS_DATASETS_DIR.rglob("*.jsonl"))

    for jsonl_path in dataset_files:
        meta_path = jsonl_path.with_suffix(".meta.json")
        if meta_path.exists():
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                did = meta.get("dataset_id")
                if did and did not in datasets_store:
                    if jsonl_path.exists():
                        datasets_store[did] = meta
                        newly_registered += 1
            except Exception:
                continue

    unregistered = sum(
        1 for p in dataset_files
        if not any(
            Path(ds.get("file_path", "")).resolve() == p.resolve()
            for ds in datasets_store.values()
        )
    )

    logger.info(
        f"Scan complete: {image_count} images, {len(dataset_files)} dataset files, "
        f"{newly_registered} newly registered, {unregistered} unregistered"
    )

    return ResponseEnvelope(
        data={
            "images_found": image_count,
            "dataset_files_found": len(dataset_files),
            "newly_registered": newly_registered,
            "unregistered": unregistered,
        }
    )
