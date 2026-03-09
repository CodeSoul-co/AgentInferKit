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

from .schemas import (
    ExperimentCreateRequest,
    ExperimentCreateResponse,
    ExperimentInfo,
    ExperimentListResponse,
    ExperimentRunResponse,
    ExperimentStopResponse,
    ResponseEnvelope,
)


router = APIRouter(tags=["experiments"])

# In-memory storage for experiments (will be replaced by database in production)
_experiments: Dict[str, Dict[str, Any]] = {}

# Directory for experiment configs
EXPERIMENTS_DIR = Path("data/experiments")


def _generate_experiment_id() -> str:
    """Generate a unique experiment ID."""
    return f"exp_{uuid.uuid4().hex[:12]}"


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
    
    # Store experiment in memory
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
    
    # Update status to running
    exp["status"] = "running"
    
    # TODO: Integrate with A组's Runner module
    # runner = get_runner(exp["dataset_id"], exp["model_id"], exp["strategy"])
    # asyncio.create_task(runner.run(experiment_id, exp))
    
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
    
    # Remove from memory
    del _experiments[experiment_id]
    
    return ResponseEnvelope(
        data={"deleted": experiment_id}
    )
