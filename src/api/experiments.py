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

from fastapi import APIRouter, Body, HTTPException, Query
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
from ..evaluators.registry import evaluate_all
from ..evaluators.group_stats import multi_group_stats
from ..config import OUTPUTS_METRICS_DIR, OUTPUTS_PREDICTIONS_DIR
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


def _resolve_dataset_path(dataset_id: str, split: str = "test") -> Optional[Path]:
    """Resolve dataset file path from dataset_id."""
    from .datasets import datasets_store
    meta = datasets_store.get(dataset_id)
    if meta and "file_path" in meta:
        return Path(meta["file_path"])
    return None


def _infer_task_type(dataset_id: str) -> str:
    """Infer task type from dataset_id string."""
    did = (dataset_id or "").lower()
    if "exam" in did or "choice" in did:
        return "text_exam"
    if "mcq" in did or "image" in did:
        return "image_mcq"
    if "agent" in did or "api" in did or "calling" in did or "tool" in did:
        return "api_calling"
    return "qa"


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
        
        # Load strategy with user-provided config
        strategy_config = exp.get("strategy_config", {})
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
        
        # Evaluate predictions and generate metrics
        logger.info(f"Evaluating experiment {experiment_id}...")
        pred_results = read_jsonl(predictions_path)
        
        # Merge reference data from samples into predictions and compute correctness
        sample_map = {s["sample_id"]: s for s in samples}
        for pred in pred_results:
            sid = pred.get("sample_id", "")
            if sid in sample_map:
                orig = sample_map[sid]
                pred.setdefault("answer", orig.get("answer", ""))
                pred.setdefault("reference_answer", orig.get("reference_answer", ""))
                pred.setdefault("question", orig.get("question", ""))
                pred.setdefault("difficulty", orig.get("difficulty", ""))
                pred.setdefault("metadata", orig.get("metadata", {}))
            # Compute per-sample correctness
            parsed = str(pred.get("parsed_answer", "")).strip()
            ref = str(pred.get("answer", pred.get("reference_answer", ""))).strip()
            if parsed and ref:
                is_correct = parsed.lower() == ref.lower()
                if not is_correct:
                    try:
                        is_correct = abs(float(parsed.replace(',', '')) - float(ref.replace(',', ''))) < 1e-6
                    except (ValueError, AttributeError):
                        pass
                pred["correct"] = is_correct
            else:
                pred["correct"] = False
        
        # Determine evaluators based on task type
        from ..evaluators.registry import list_metrics
        available_metrics = set(list_metrics())
        
        eval_config = exp.get("eval", {})
        evaluator_names = eval_config.get("metrics", [])
        # Filter out invalid metric names
        evaluator_names = [m for m in evaluator_names if m in available_metrics]
        
        if not evaluator_names:
            if task_type in ("text_exam", "image_mcq"):
                evaluator_names = ["choice_accuracy", "option_bias", "latency_stats", "token_stats", "cost_estimate"]
            elif task_type == "api_calling":
                evaluator_names = ["tool_selection_accuracy", "parameter_accuracy", "end_to_end_success_rate", "invalid_call_rate", "avg_tool_calls", "latency_stats", "token_stats", "cost_estimate"]
            else:
                evaluator_names = ["exact_match", "f1_score", "bleu", "rouge_l", "latency_stats", "token_stats", "cost_estimate"]
            # Auto-add reasoning step metric for non-direct strategies
            strategy_name = exp.get("strategy", "direct")
            if strategy_name in ("cot", "long_cot", "tot", "self_refine", "self_consistency", "react"):
                evaluator_names.append("avg_reasoning_steps")
            # Auto-add RAG metrics when RAG retrieval is enabled
            rag_cfg = exp.get("rag", {})
            if rag_cfg.get("enabled") and rag_cfg.get("mode") == "retrieved":
                evaluator_names.extend(["retrieval_hit_rate", "context_relevance", "retrieval_recall_at_k", "answer_evidence_consistency", "hallucination_rate"])
        
        # Deduplicate while preserving order
        seen = set()
        evaluator_names = [m for m in evaluator_names if m in available_metrics and not (m in seen or seen.add(m))]
        
        logger.info(f"Using evaluators: {evaluator_names}")
        metric_results = evaluate_all(pred_results, evaluator_names, {})
        
        # Write enriched predictions back (with correct, answer, question fields)
        with open(predictions_path, "w", encoding="utf-8") as f:
            for pred in pred_results:
                f.write(json.dumps(pred, ensure_ascii=False) + "\n")
        
        # Build overall summary
        valid_samples = sum(1 for p in pred_results if not p.get("error"))
        overall = {}
        for name, result in metric_results.items():
            if isinstance(result, dict):
                # Extract the primary score from different metric result formats
                for score_key in ("score", "accuracy", "avg_f1", "avg_bleu",
                                  "avg_rouge_l_f1", "avg_score",
                                  "hit_rate", "success_rate", "rate"):
                    if score_key in result:
                        overall[name] = result[score_key]
                        break
                # Extract efficiency stats into overall
                if name == "latency_stats":
                    if "avg_ms" in result:
                        overall["avg_latency_ms"] = result["avg_ms"]
                elif name == "token_stats":
                    if "avg_total_tokens" in result:
                        overall["avg_tokens"] = result["avg_total_tokens"]
                    elif "avg_total" in result:
                        overall["avg_tokens"] = result["avg_total"]
                elif name == "cost_estimate":
                    if "estimated_cost_usd" in result:
                        overall["total_cost_usd"] = result["estimated_cost_usd"]
                    elif "total_usd" in result:
                        overall["total_cost_usd"] = result["total_usd"]
            elif isinstance(result, (int, float)):
                overall[name] = result
        
        overall["valid_samples"] = valid_samples
        overall["total_samples"] = len(samples)
        
        # Group stats
        group_by = eval_config.get("group_by", ["difficulty"])
        try:
            grouped = multi_group_stats(pred_results, samples, group_by)
        except Exception as ge:
            logger.warning(f"Group stats failed: {ge}")
            grouped = {}
        
        # Build metrics output
        from datetime import timezone
        metrics_output = {
            "experiment_id": experiment_id,
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "model": exp["model_id"],
            "strategy": exp["strategy"],
            "dataset": str(dataset_path),
            "total_samples": len(samples),
            "valid_samples": valid_samples,
            "overall": overall,
        }
        metrics_output.update(grouped)
        for name, result in metric_results.items():
            if name not in overall:
                metrics_output[name] = result
        
        # Write metrics file
        OUTPUTS_METRICS_DIR.mkdir(parents=True, exist_ok=True)
        metrics_path = OUTPUTS_METRICS_DIR / f"{experiment_id}.json"
        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(metrics_output, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Metrics written to {metrics_path}")
        
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


@router.get(
    "/strategies",
    response_model=ResponseEnvelope,
    summary="List available strategies and their configurable parameters",
)
async def list_strategy_params():
    """
    Return all available inference strategies with their configurable parameters.

    Each parameter includes: name, type, default, description, and optional
    constraints (min, max, options). The frontend can use this to render
    dynamic parameter forms when a user selects a strategy.
    """
    from ..strategies.registry import list_strategies
    from ..strategies.params import get_strategy_params

    result = []
    for name in list_strategies():
        result.append({
            "name": name,
            "params": get_strategy_params(name),
        })
    return ResponseEnvelope(data=result)


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
        "strategy_config": request.strategy_config,
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
    
    # Allow re-running finished, failed, or stopped experiments (reset state)
    if exp["status"] in ("finished", "failed", "stopped"):
        exp["completed"] = 0
        exp["total_samples"] = 0
        exp["finished_at"] = None
        # Clean up old predictions and progress so batch starts fresh
        old_pred = Path("outputs/predictions") / f"{experiment_id}.jsonl"
        old_prog = Path("outputs/predictions") / f"{experiment_id}_progress.json"
        for p in (old_pred, old_prog):
            if p.exists():
                p.unlink()
    
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
    
    # Signal batch runner to stop processing new samples
    from src.runners.batch_runner import cancel_experiment
    cancel_experiment(experiment_id)
    
    # Update status
    exp["status"] = "stopped"
    _save_experiments()
    
    return ResponseEnvelope(
        data=ExperimentStopResponse(
            status="stopped",
            completed=exp["completed"],
        )
    )


@router.post(
    "/{experiment_id}/evaluate",
    response_model=ResponseEnvelope[Dict[str, Any]],
    summary="Run evaluation on existing predictions",
)
async def evaluate_experiment(experiment_id: str, body: Dict[str, Any] = Body(default={})):
    """
    Run evaluation on an existing experiment's predictions.
    Accepts optional metrics list and group_by dimensions.
    """
    exp = _get_experiment_or_404(experiment_id)

    if exp["status"] != "finished":
        raise HTTPException(status_code=409, detail="Experiment must be finished before evaluation")

    predictions_path = Path("outputs/predictions") / f"{experiment_id}.jsonl"
    if not predictions_path.exists():
        raise HTTPException(status_code=404, detail="Predictions file not found")

    pred_results = read_jsonl(predictions_path)

    # Load original samples to merge reference data
    dataset_id = exp.get("dataset_id", "")
    split = exp.get("split", "test")
    dataset_path = _resolve_dataset_path(dataset_id, split)
    samples = []
    if dataset_path and dataset_path.exists():
        samples = read_jsonl(str(dataset_path))

    sample_map = {s.get("sample_id", s.get("id", "")): s for s in samples}
    for pred in pred_results:
        sid = pred.get("sample_id", "")
        if sid in sample_map:
            orig = sample_map[sid]
            pred.setdefault("answer", orig.get("answer", ""))
            pred.setdefault("reference_answer", orig.get("reference_answer", ""))
            pred.setdefault("question", orig.get("question", ""))
            pred.setdefault("difficulty", orig.get("difficulty", ""))
            pred.setdefault("metadata", orig.get("metadata", {}))
        # Compute per-sample correctness
        parsed = str(pred.get("parsed_answer", "")).strip()
        ref = str(pred.get("answer", pred.get("reference_answer", ""))).strip()
        if parsed and ref:
            is_correct = parsed.lower() == ref.lower()
            if not is_correct:
                try:
                    is_correct = abs(float(parsed.replace(',', '')) - float(ref.replace(',', ''))) < 1e-6
                except (ValueError, AttributeError):
                    pass
            pred["correct"] = is_correct
        else:
            pred["correct"] = False

    # Determine evaluators
    from ..evaluators.registry import list_metrics
    available_metrics = set(list_metrics())

    requested_metrics = body.get("metrics", [])
    evaluator_names = [m for m in requested_metrics if m in available_metrics]

    if not evaluator_names:
        task_type = _infer_task_type(dataset_id)
        if task_type in ("text_exam", "image_mcq"):
            evaluator_names = ["choice_accuracy", "option_bias", "latency_stats", "token_stats", "cost_estimate"]
        elif task_type == "api_calling":
            evaluator_names = ["tool_selection_accuracy", "parameter_accuracy", "end_to_end_success_rate",
                               "invalid_call_rate", "avg_tool_calls", "latency_stats", "token_stats", "cost_estimate"]
        else:
            evaluator_names = ["exact_match", "f1_score", "bleu", "rouge_l", "latency_stats", "token_stats", "cost_estimate"]
        # Auto-add reasoning step metric for non-direct strategies
        strategy_name = exp.get("strategy", "direct")
        if strategy_name in ("cot", "long_cot", "tot", "self_refine", "self_consistency", "react"):
            evaluator_names.append("avg_reasoning_steps")
        # Auto-add RAG metrics when RAG retrieval is enabled
        rag_cfg = exp.get("rag", {})
        if rag_cfg.get("enabled") and rag_cfg.get("mode") == "retrieved":
            evaluator_names.extend(["retrieval_hit_rate", "context_relevance", "retrieval_recall_at_k", "answer_evidence_consistency", "hallucination_rate"])

    # Deduplicate while preserving order
    seen = set()
    evaluator_names = [m for m in evaluator_names if m in available_metrics and not (m in seen or seen.add(m))]

    logger.info(f"Evaluate {experiment_id} with: {evaluator_names}")
    metric_results = evaluate_all(pred_results, evaluator_names, {})

    # Write enriched predictions back (with correct, answer, question fields)
    pred_file = OUTPUTS_PREDICTIONS_DIR / f"{experiment_id}.jsonl"
    if pred_file.exists():
        with open(pred_file, "w", encoding="utf-8") as f:
            for pred in pred_results:
                f.write(json.dumps(pred, ensure_ascii=False) + "\n")

    # Build overall summary
    valid_samples = sum(1 for p in pred_results if not p.get("error"))
    overall = {}
    for name, result in metric_results.items():
        if isinstance(result, dict):
            for score_key in ("score", "accuracy", "avg_f1", "avg_bleu",
                              "avg_rouge_l_f1", "avg_score",
                              "hit_rate", "success_rate", "rate"):
                if score_key in result:
                    overall[name] = result[score_key]
                    break
            if name == "latency_stats" and "avg_ms" in result:
                overall["avg_latency_ms"] = result["avg_ms"]
            elif name == "token_stats":
                overall["avg_tokens"] = result.get("avg_total_tokens", result.get("avg_total", 0))
            elif name == "cost_estimate":
                overall["total_cost_usd"] = result.get("estimated_cost_usd", result.get("total_usd", 0))
        elif isinstance(result, (int, float)):
            overall[name] = result

    overall["valid_samples"] = valid_samples
    overall["total_samples"] = len(pred_results)

    # Group stats
    group_by = body.get("group_by", ["difficulty"])
    try:
        grouped = multi_group_stats(pred_results, samples, group_by)
    except Exception as ge:
        logger.warning(f"Group stats failed: {ge}")
        grouped = {}

    from datetime import timezone
    metrics_output = {
        "experiment_id": experiment_id,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "model": exp.get("model_id", ""),
        "strategy": exp.get("strategy", ""),
        "dataset": dataset_id,
        "total_samples": len(pred_results),
        "valid_samples": valid_samples,
        "overall": overall,
    }
    metrics_output.update(grouped)
    for name, result in metric_results.items():
        if name not in overall:
            metrics_output[name] = result

    OUTPUTS_METRICS_DIR.mkdir(parents=True, exist_ok=True)
    metrics_path = OUTPUTS_METRICS_DIR / f"{experiment_id}.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_output, f, ensure_ascii=False, indent=2)

    # Clear metrics cache in results module
    from .results import metrics_store
    if experiment_id in metrics_store:
        del metrics_store[experiment_id]

    logger.info(f"Evaluation written to {metrics_path}")

    return ResponseEnvelope(data={"experiment_id": experiment_id, "metrics_path": str(metrics_path), "status": "evaluated"})


@router.delete(
    "/{experiment_id}",
    response_model=ResponseEnvelope[Dict[str, str]],
    summary="Delete an experiment",
)
async def delete_experiment(experiment_id: str):
    """
    Delete an experiment and all associated data (config, predictions, metrics, progress).
    
    Running experiments are automatically stopped before deletion.
    """
    exp = _get_experiment_or_404(experiment_id)
    
    # Auto-stop running experiments instead of blocking deletion
    if exp["status"] == "running":
        from src.runners.batch_runner import cancel_experiment
        cancel_experiment(experiment_id)
        exp["status"] = "stopped"
        logger.info(f"Auto-stopped running experiment {experiment_id} for deletion")
    
    # Delete config file
    config_path = Path(exp.get("config_path", ""))
    if config_path.exists():
        config_path.unlink()
    
    # Delete prediction files
    pred_file = OUTPUTS_PREDICTIONS_DIR / f"{experiment_id}.jsonl"
    prog_file = OUTPUTS_PREDICTIONS_DIR / f"{experiment_id}_progress.json"
    for p in (pred_file, prog_file):
        if p.exists():
            p.unlink()
    
    # Delete metrics file
    metrics_file = OUTPUTS_METRICS_DIR / f"{experiment_id}.json"
    if metrics_file.exists():
        metrics_file.unlink()
    
    # Remove from memory and persist
    del _experiments[experiment_id]
    _save_experiments()
    
    return ResponseEnvelope(
        data={"deleted": experiment_id}
    )
