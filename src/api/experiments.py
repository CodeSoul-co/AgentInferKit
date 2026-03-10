"""
Experiments API routes.

Implements: experiment creation, listing, details, run, stop, delete.
Provides SSE endpoint for real-time progress updates.
"""

import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from loguru import logger

from .schemas import (
    ExperimentCreateRequest,
    ExperimentCreateResponse,
    ExperimentInfo,
    ExperimentListResponse,
    ExperimentRunResponse,
    ExperimentStopResponse,
    ResponseEnvelope,
)
from ..runners.batch_runner import BatchRunner
from ..runners.qa_runner import QARunner
from ..runners.exam_runner import ExamRunner
from ..runners.image_runner import ImageRunner
from ..runners.agent_runner import AgentRunner
from ..adapters.registry import load_adapter
from ..strategies.registry import load_strategy
from ..utils.file_io import read_jsonl


router = APIRouter(tags=["experiments"])

# Directory for experiment configs and state
EXPERIMENTS_DIR = Path("data/experiments")
_STATE_FILE = EXPERIMENTS_DIR / "_state.json"


def _load_experiments() -> Dict[str, Dict[str, Any]]:
    """Load experiments from persistent JSON state file."""
    if not _STATE_FILE.exists():
        return {}
    try:
        with open(_STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Restore datetime objects
        for exp in data.values():
            if isinstance(exp.get("created_at"), str):
                exp["created_at"] = datetime.fromisoformat(exp["created_at"])
            if isinstance(exp.get("finished_at"), str):
                exp["finished_at"] = datetime.fromisoformat(exp["finished_at"])
        return data
    except (json.JSONDecodeError, OSError):
        return {}


def _save_experiments() -> None:
    """Persist experiments dict to JSON state file."""
    EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)
    serialisable = {}
    for eid, exp in _experiments.items():
        row = dict(exp)
        if isinstance(row.get("created_at"), datetime):
            row["created_at"] = row["created_at"].isoformat()
        if isinstance(row.get("finished_at"), datetime):
            row["finished_at"] = row["finished_at"].isoformat()
        serialisable[eid] = row
    with open(_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(serialisable, f, indent=2, ensure_ascii=False)


_experiments: Dict[str, Dict[str, Any]] = _load_experiments()


def _generate_experiment_id() -> str:
    """Generate a unique experiment ID."""
    return f"exp_{uuid.uuid4().hex[:12]}"


async def _run_experiment_task(experiment_id: str, exp: Dict[str, Any]):
    """Background task to run experiment inference."""
    try:
        logger.info(f"Starting experiment {experiment_id}")
        
        # Load dataset - get file_path from datasets_store
        from .datasets import datasets_store
        dataset_meta = datasets_store.get(exp['dataset_id'])
        if not dataset_meta:
            logger.error(f"Dataset metadata not found: {exp['dataset_id']}")
            exp["status"] = "failed"
            _save_experiments()
            return
        
        dataset_path = Path(dataset_meta['file_path'])
        if not dataset_path.exists():
            logger.error(f"Dataset file not found: {dataset_path}")
            exp["status"] = "failed"
            _save_experiments()
            return
        
        samples = read_jsonl(dataset_path)
        max_samples = exp.get("max_samples")
        if max_samples and max_samples > 0:
            samples = samples[:max_samples]
        
        # Update total_samples
        exp["total_samples"] = len(samples)
        exp["completed"] = 0
        _save_experiments()
        
        logger.info(f"Loaded {len(samples)} samples for experiment {experiment_id}")
        
        # Determine task type from dataset metadata or first sample
        task_type = dataset_meta.get("task_type") or (samples[0].get("task_type", "text_qa") if samples else "text_qa")
        
        # Load model adapter
        model_config = {
            "provider": exp["model_id"].split("-")[0] if "-" in exp["model_id"] else "openai",
            "model": exp["model_id"]
        }
        adapter = load_adapter(model_config)
        
        # Load strategy
        strategy_config = {}
        strategy = load_strategy(exp["strategy"], strategy_config)
        
        # Create appropriate runner
        rag_config = exp.get("rag", {})
        if task_type == "api_calling":
            runner = AgentRunner(adapter, strategy, model_config=model_config, rag_config=rag_config)
        elif task_type in ("text_exam", "image_mcq"):
            runner = ExamRunner(adapter, strategy, model_config=model_config, rag_config=rag_config)
        else:
            runner = QARunner(adapter, strategy, model_config=model_config, rag_config=rag_config)
        
        # Run batch inference
        batch_runner = BatchRunner(
            experiment_id=experiment_id,
            model_name=exp["model_id"],
            strategy_name=exp["strategy"]
        )
        
        def on_progress(completed: int, total: int, failed: int):
            exp["completed"] = completed
            _save_experiments()
            logger.info(f"Progress: {completed}/{total} (failed: {failed})")
        
        concurrency = exp.get("runner", {}).get("concurrency", 5)
        predictions_path = await batch_runner.run(
            runner=runner,
            samples=samples,
            experiment_id=experiment_id,
            concurrency=concurrency,
            on_progress=on_progress
        )
        
        # Mark as finished
        exp["status"] = "finished"
        exp["finished_at"] = datetime.now()
        _save_experiments()
        
        logger.info(f"Experiment {experiment_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Experiment {experiment_id} failed: {e}", exc_info=True)
        exp["status"] = "failed"
        _save_experiments()


def _get_experiment_or_404(experiment_id: str) -> Dict[str, Any]:
    """Get experiment by ID or raise 404."""
    if experiment_id not in _experiments:
        raise HTTPException(status_code=404, detail=f"Experiment '{experiment_id}' not found")
    return _experiments[experiment_id]


@router.post(
    "",
    response_model=ResponseEnvelope[ExperimentCreateResponse],
    summary="Create a new experiment",
)
async def create_experiment(request: ExperimentCreateRequest):
    """
    Create a new experiment configuration.
    
    The experiment is created in 'created' status and must be started
    separately via the /run endpoint.
    """
    experiment_id = _generate_experiment_id()
    
    # Ensure experiments directory exists
    EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save config snapshot
    config_path = EXPERIMENTS_DIR / f"{experiment_id}_config.json"
    config_data = request.model_dump()
    config_data["experiment_id"] = experiment_id
    config_data["created_at"] = datetime.now().isoformat()
    
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    # Store experiment and persist
    _experiments[experiment_id] = {
        "experiment_id": experiment_id,
        "name": request.name,
        "description": request.description,
        "status": "created",
        "dataset_id": request.dataset_id,
        "split": request.split,
        "max_samples": request.max_samples,
        "model_id": request.model_id,
        "strategy": request.strategy,
        "rag": request.rag.model_dump(),
        "runner": request.runner.model_dump(),
        "eval": request.eval.model_dump(),
        "seed": request.seed,
        "total_samples": 0,  # Will be set when run starts
        "completed": 0,
        "created_at": datetime.now(),
        "finished_at": None,
        "config_path": str(config_path),
    }
    _save_experiments()
    
    return ResponseEnvelope(
        data=ExperimentCreateResponse(
            experiment_id=experiment_id,
            status="created",
            config_snapshot_path=str(config_path),
        )
    )


@router.get(
    "",
    response_model=ResponseEnvelope[ExperimentListResponse],
    summary="List all experiments",
)
async def list_experiments(
    status: Optional[str] = Query(None, description="Filter by status"),
    dataset_id: Optional[str] = Query(None, description="Filter by dataset ID"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """
    List all experiments with optional filtering.
    """
    experiments = list(_experiments.values())
    
    # Apply filters
    if status:
        experiments = [e for e in experiments if e["status"] == status]
    if dataset_id:
        experiments = [e for e in experiments if e["dataset_id"] == dataset_id]
    
    # Sort by creation time (newest first)
    experiments.sort(key=lambda x: x["created_at"], reverse=True)
    
    # Apply pagination
    paginated = experiments[offset:offset + limit]
    
    # Convert to response model
    experiment_infos = [
        ExperimentInfo(
            experiment_id=e["experiment_id"],
            name=e["name"],
            status=e["status"],
            dataset_id=e["dataset_id"],
            model_id=e["model_id"],
            strategy=e["strategy"],
            total_samples=e["total_samples"],
            completed=e["completed"],
            created_at=e["created_at"],
            finished_at=e.get("finished_at"),
        )
        for e in paginated
    ]
    
    return ResponseEnvelope(
        data=ExperimentListResponse(experiments=experiment_infos)
    )


@router.get(
    "/{experiment_id}",
    response_model=ResponseEnvelope[ExperimentInfo],
    summary="Get experiment details",
)
async def get_experiment(experiment_id: str):
    """
    Get detailed information about a specific experiment.
    """
    exp = _get_experiment_or_404(experiment_id)
    
    return ResponseEnvelope(
        data=ExperimentInfo(
            experiment_id=exp["experiment_id"],
            name=exp["name"],
            status=exp["status"],
            dataset_id=exp["dataset_id"],
            model_id=exp["model_id"],
            strategy=exp["strategy"],
            total_samples=exp["total_samples"],
            completed=exp["completed"],
            created_at=exp["created_at"],
            finished_at=exp.get("finished_at"),
        )
    )


@router.post(
    "/{experiment_id}/run",
    response_model=ResponseEnvelope[ExperimentRunResponse],
    summary="Start experiment execution",
)
async def run_experiment(experiment_id: str):
    """
    Start running an experiment.
    
    Returns an SSE stream URL for real-time progress updates.
    The actual execution is delegated to A组's Runner module.
    """
    exp = _get_experiment_or_404(experiment_id)
    
    if exp["status"] == "running":
        raise HTTPException(status_code=409, detail="Experiment is already running")
    if exp["status"] == "finished":
        raise HTTPException(status_code=409, detail="Experiment has already finished")
    
    # Allow re-running failed experiments
    if exp["status"] == "failed":
        exp["completed"] = 0
        exp["total_samples"] = 0
        exp["finished_at"] = None
    
    # Update status to running
    exp["status"] = "running"
    _save_experiments()
    
    # Start experiment execution in background
    asyncio.create_task(_run_experiment_task(experiment_id, exp))
    
    stream_url = f"/{experiment_id}/progress"
    
    return ResponseEnvelope(
        data=ExperimentRunResponse(
            experiment_id=experiment_id,
            status="running",
            stream_url=stream_url,
        )
    )


@router.get(
    "/{experiment_id}/progress",
    summary="SSE endpoint for experiment progress",
)
async def experiment_progress(experiment_id: str):
    """
    Server-Sent Events endpoint for real-time experiment progress.
    
    Event types:
    - progress: {completed, total, current_sample_id, accuracy}
    - sample: {sample_id, prediction, correct, latency_ms}
    - done: {final_metrics}
    - error: {message}
    """
    exp = _get_experiment_or_404(experiment_id)
    
    async def event_generator():
        """Generate SSE events for experiment progress."""
        try:
            # Send initial status
            yield f"event: progress\ndata: {json.dumps({'completed': exp['completed'], 'total': exp['total_samples'], 'status': exp['status']})}\n\n"
            
            # TODO: Integrate with A组's Runner module for real progress
            # This is a mock implementation for demonstration
            while exp["status"] == "running":
                await asyncio.sleep(1)
                
                # Check if experiment is still running
                if experiment_id not in _experiments:
                    yield f"event: error\ndata: {json.dumps({'message': 'Experiment not found'})}\n\n"
                    break
                
                current_exp = _experiments[experiment_id]
                
                if current_exp["status"] != "running":
                    break
                
                # Send progress update
                yield f"event: progress\ndata: {json.dumps({'completed': current_exp['completed'], 'total': current_exp['total_samples'], 'status': current_exp['status']})}\n\n"
            
            # Send completion event
            final_exp = _experiments.get(experiment_id, exp)
            yield f"event: done\ndata: {json.dumps({'status': final_exp['status'], 'completed': final_exp['completed']})}\n\n"
            
        except asyncio.CancelledError:
            yield f"event: error\ndata: {json.dumps({'message': 'Connection closed'})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post(
    "/{experiment_id}/stop",
    response_model=ResponseEnvelope[ExperimentStopResponse],
    summary="Stop a running experiment",
)
async def stop_experiment(experiment_id: str):
    """
    Stop a running experiment.
    
    The experiment can be resumed later if runner.resume is enabled.
    """
    exp = _get_experiment_or_404(experiment_id)
    
    if exp["status"] != "running":
        raise HTTPException(status_code=409, detail=f"Experiment is not running (status: {exp['status']})")
    
    # Update status
    exp["status"] = "stopped"
    _save_experiments()
    
    # TODO: Integrate with A组's Runner module to stop execution
    # runner.stop(experiment_id)
    
    return ResponseEnvelope(
        data=ExperimentStopResponse(
            status="stopped",
            completed=exp["completed"],
        )
    )


@router.delete(
    "/{experiment_id}",
    response_model=ResponseEnvelope[Dict[str, str]],
    summary="Delete an experiment",
)
async def delete_experiment(experiment_id: str):
    """
    Delete an experiment and its associated data.
    
    Running experiments must be stopped first.
    """
    exp = _get_experiment_or_404(experiment_id)
    
    if exp["status"] == "running":
        raise HTTPException(status_code=409, detail="Cannot delete a running experiment. Stop it first.")
    
    # Delete config file if exists
    config_path = Path(exp.get("config_path", ""))
    if config_path.exists():
        config_path.unlink()
    
    # Remove from memory and persist
    del _experiments[experiment_id]
    _save_experiments()
    
    return ResponseEnvelope(
        data={"deleted": experiment_id}
    )
