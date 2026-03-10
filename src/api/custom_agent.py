"""
Custom Agent API — allows external agents (e.g. OpenClaw) to interact
with our benchmark platform.

Flow:
  1. POST /agent/sessions        — create a session, get samples to solve
  2. POST /agent/sessions/{id}/tool_call — call a tool, get observation back
  3. POST /agent/sessions/{id}/submit    — submit final answer for a sample
  4. POST /agent/sessions/{id}/finish    — mark session done, trigger eval
  5. GET  /agent/sessions/{id}/results   — retrieve evaluation metrics

The external agent drives the reasoning loop; our platform provides:
  - Dataset samples
  - Tool execution (mock or real)
  - Evaluation of submitted predictions
"""

import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel, Field

from .schemas import ResponseEnvelope

router = APIRouter(tags=["custom_agent"])

# ---------------------------------------------------------------------------
# In-memory session store
# ---------------------------------------------------------------------------
_sessions: Dict[str, Dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------

class AgentSessionCreateRequest(BaseModel):
    """Create a new agent evaluation session."""
    agent_name: str = Field(..., description="Name of the external agent (e.g. 'openclaw-v1')")
    dataset_path: str = Field(..., description="Path to dataset JSONL to evaluate on")
    max_samples: Optional[int] = Field(default=None, ge=1, description="Limit number of samples")
    evaluators: List[str] = Field(
        default=["choice_accuracy", "exact_match", "latency_stats"],
        description="Evaluator metrics to run on finish"
    )
    group_by: List[str] = Field(
        default=["difficulty", "metadata.topic"],
        description="Grouping dimensions for evaluation"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary metadata about this agent run")


class AgentSessionCreateResponse(BaseModel):
    """Response after session creation."""
    session_id: str
    agent_name: str
    total_samples: int
    samples: List[Dict[str, Any]] = Field(
        description="The samples the agent should solve. Each has sample_id, task_type, question, etc."
    )


class ToolCallRequest(BaseModel):
    """Agent requests a tool execution."""
    sample_id: str = Field(..., description="Which sample this tool call belongs to")
    tool_id: str = Field(..., description="Tool to invoke")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")


class ToolCallResponse(BaseModel):
    """Tool execution result."""
    tool_id: str
    observation: Any = Field(description="Tool output / observation")
    success: bool = True
    error: Optional[str] = None


class SubmitAnswerRequest(BaseModel):
    """Agent submits a final answer for one sample."""
    sample_id: str = Field(..., description="Sample being answered")
    parsed_answer: str = Field(..., description="Agent's final answer")
    raw_output: str = Field(default="", description="Full agent output / reasoning text")
    reasoning_trace: Any = Field(default=None, description="Structured reasoning trace")
    tool_trace: List[Dict[str, Any]] = Field(default_factory=list, description="Tool calls made")
    usage: Dict[str, Any] = Field(default_factory=dict, description="Token/latency usage from agent side")


class SubmitAnswerResponse(BaseModel):
    """Acknowledgement of answer submission."""
    sample_id: str
    accepted: bool = True
    submitted_count: int = Field(description="Total answers submitted so far")
    remaining_count: int = Field(description="Samples still pending")


class SessionFinishResponse(BaseModel):
    """Response after finishing a session — includes evaluation results."""
    session_id: str
    agent_name: str
    total_samples: int
    submitted: int
    metrics_path: str
    overall: Dict[str, Any]


class SessionStatusResponse(BaseModel):
    """Current session status."""
    session_id: str
    agent_name: str
    status: str
    total_samples: int
    submitted: int
    created_at: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/sessions",
    response_model=ResponseEnvelope[AgentSessionCreateResponse],
    summary="Create agent evaluation session",
)
async def create_session(request: AgentSessionCreateRequest):
    """
    Create a session for an external agent. Returns the dataset samples
    the agent should solve. The agent then calls tool_call / submit / finish.
    """
    from src.utils.file_io import read_jsonl

    if not Path(request.dataset_path).exists():
        raise HTTPException(status_code=404, detail=f"Dataset not found: {request.dataset_path}")

    samples = read_jsonl(request.dataset_path)
    if request.max_samples:
        samples = samples[:request.max_samples]

    session_id = f"agent_{uuid.uuid4().hex[:12]}"

    # Strip ground truth from samples sent to agent
    agent_samples = []
    for s in samples:
        visible = dict(s)
        visible.pop("answer", None)
        visible.pop("reference_answer", None)
        visible.pop("ground_truth", None)
        agent_samples.append(visible)

    _sessions[session_id] = {
        "session_id": session_id,
        "agent_name": request.agent_name,
        "dataset_path": request.dataset_path,
        "samples": samples,  # full samples with answers (for eval)
        "agent_samples": agent_samples,
        "predictions": {},  # sample_id -> prediction dict
        "tool_traces": {},  # sample_id -> list of tool calls
        "evaluators": request.evaluators,
        "group_by": request.group_by,
        "metadata": request.metadata,
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info(f"Agent session created: {session_id} ({request.agent_name}, {len(samples)} samples)")

    return ResponseEnvelope(data=AgentSessionCreateResponse(
        session_id=session_id,
        agent_name=request.agent_name,
        total_samples=len(samples),
        samples=agent_samples,
    ))


@router.post(
    "/sessions/{session_id}/tool_call",
    response_model=ResponseEnvelope[ToolCallResponse],
    summary="Execute a tool call",
)
async def tool_call(session_id: str, request: ToolCallRequest):
    """
    Agent requests a tool execution. We run it through the mock executor
    and return the observation.
    """
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
    if session["status"] != "active":
        raise HTTPException(status_code=409, detail="Session is not active")

    try:
        from src.toolsim.registry import ToolRegistry
        from src.toolsim.executor import MockExecutor

        registry = ToolRegistry()
        executor = MockExecutor(registry)
        result = executor.execute(request.tool_id, request.parameters)

        # Track tool trace
        trace_entry = {
            "tool_id": request.tool_id,
            "parameters": request.parameters,
            "observation": result,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        session["tool_traces"].setdefault(request.sample_id, []).append(trace_entry)

        return ResponseEnvelope(data=ToolCallResponse(
            tool_id=request.tool_id,
            observation=result,
            success=True,
        ))
    except Exception as e:
        return ResponseEnvelope(data=ToolCallResponse(
            tool_id=request.tool_id,
            observation=None,
            success=False,
            error=str(e),
        ))


@router.post(
    "/sessions/{session_id}/submit",
    response_model=ResponseEnvelope[SubmitAnswerResponse],
    summary="Submit answer for a sample",
)
async def submit_answer(session_id: str, request: SubmitAnswerRequest):
    """
    Agent submits its final answer for one sample.
    """
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
    if session["status"] != "active":
        raise HTTPException(status_code=409, detail="Session is not active")

    # Validate sample_id belongs to this session
    valid_ids = {s["sample_id"] for s in session["samples"]}
    if request.sample_id not in valid_ids:
        raise HTTPException(status_code=400, detail=f"sample_id '{request.sample_id}' not in this session")

    # Build prediction dict
    prediction = {
        "sample_id": request.sample_id,
        "experiment_id": session_id,
        "model": session["agent_name"],
        "strategy": "custom_agent",
        "prompt_id": "",
        "prompt_version": "",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input_prompt": "",
        "raw_output": request.raw_output,
        "parsed_answer": request.parsed_answer,
        "reasoning_trace": request.reasoning_trace or [],
        "rag_context": {"mode": None, "retrieved_chunks": []},
        "tool_trace": request.tool_trace or session["tool_traces"].get(request.sample_id, []),
        "usage": request.usage,
        "error": None,
    }

    session["predictions"][request.sample_id] = prediction
    submitted = len(session["predictions"])
    remaining = len(session["samples"]) - submitted

    logger.info(f"Session {session_id}: submitted {request.sample_id} ({submitted}/{len(session['samples'])})")

    return ResponseEnvelope(data=SubmitAnswerResponse(
        sample_id=request.sample_id,
        accepted=True,
        submitted_count=submitted,
        remaining_count=remaining,
    ))


@router.post(
    "/sessions/{session_id}/finish",
    response_model=ResponseEnvelope[SessionFinishResponse],
    summary="Finish session and run evaluation",
)
async def finish_session(session_id: str):
    """
    Mark the session as done and run evaluation on submitted predictions.
    Returns overall metrics.
    """
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    session["status"] = "finished"

    predictions = list(session["predictions"].values())
    samples = session["samples"]
    evaluators = session["evaluators"]
    group_by = session["group_by"]

    if not predictions:
        raise HTTPException(status_code=400, detail="No predictions submitted")

    # Merge reference data into predictions for evaluation
    sample_map = {s["sample_id"]: s for s in samples}
    for pred in predictions:
        sid = pred.get("sample_id", "")
        if sid in sample_map:
            orig = sample_map[sid]
            pred.setdefault("answer", orig.get("answer", ""))
            pred.setdefault("reference_answer", orig.get("reference_answer", ""))
            pred.setdefault("difficulty", orig.get("difficulty", ""))
            pred.setdefault("metadata", orig.get("metadata", {}))

    # Run evaluation
    from src.evaluators.registry import evaluate_all
    from src.evaluators.group_stats import multi_group_stats
    from src.config import OUTPUTS_METRICS_DIR, OUTPUTS_PREDICTIONS_DIR
    from src.utils.file_io import write_jsonl

    metric_results = evaluate_all(predictions, evaluators, {})

    # Build overall
    overall: Dict[str, Any] = {}
    if "choice_accuracy" in metric_results:
        overall["accuracy"] = metric_results["choice_accuracy"].get("accuracy", 0.0)
    elif "exact_match" in metric_results:
        overall["accuracy"] = metric_results["exact_match"].get("accuracy", 0.0)
    if "f1_score" in metric_results:
        overall["f1"] = metric_results["f1_score"].get("avg_f1", 0.0)
    if "latency_stats" in metric_results:
        overall["avg_latency_ms"] = metric_results["latency_stats"].get("avg_ms", 0)
    if "token_stats" in metric_results:
        overall["avg_tokens"] = metric_results["token_stats"].get("avg_total_tokens", 0)

    # Grouped stats
    grouped = multi_group_stats(predictions, samples, group_by) if group_by else {}

    # Write predictions + metrics
    pred_dir = OUTPUTS_PREDICTIONS_DIR
    pred_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(str(pred_dir / f"{session_id}.jsonl"), predictions)

    metrics_dir = OUTPUTS_METRICS_DIR
    metrics_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = metrics_dir / f"{session_id}.json"

    metrics_output = {
        "experiment_id": session_id,
        "agent_name": session["agent_name"],
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "dataset": session["dataset_path"],
        "total_samples": len(samples),
        "submitted": len(predictions),
        "overall": overall,
        "metadata": session["metadata"],
    }
    metrics_output.update(grouped)

    for name, result in metric_results.items():
        if name not in ("choice_accuracy", "exact_match", "f1_score",
                         "latency_stats", "token_stats", "cost_estimate"):
            metrics_output[name] = result

    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_output, f, ensure_ascii=False, indent=2)

    logger.info(f"Session {session_id} finished: {len(predictions)}/{len(samples)} evaluated, overall={overall}")

    return ResponseEnvelope(data=SessionFinishResponse(
        session_id=session_id,
        agent_name=session["agent_name"],
        total_samples=len(samples),
        submitted=len(predictions),
        metrics_path=str(metrics_path),
        overall=overall,
    ))


@router.get(
    "/sessions/{session_id}",
    response_model=ResponseEnvelope[SessionStatusResponse],
    summary="Get session status",
)
async def get_session(session_id: str):
    """Get current status of an agent session."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    return ResponseEnvelope(data=SessionStatusResponse(
        session_id=session_id,
        agent_name=session["agent_name"],
        status=session["status"],
        total_samples=len(session["samples"]),
        submitted=len(session["predictions"]),
        created_at=session["created_at"],
    ))


@router.get(
    "/sessions/{session_id}/results",
    response_model=ResponseEnvelope[Dict[str, Any]],
    summary="Get session evaluation results",
)
async def get_results(session_id: str):
    """Get evaluation results for a finished session."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
    if session["status"] != "finished":
        raise HTTPException(status_code=409, detail="Session not finished yet. Call /finish first.")

    from src.config import OUTPUTS_METRICS_DIR
    metrics_path = OUTPUTS_METRICS_DIR / f"{session_id}.json"
    if not metrics_path.exists():
        raise HTTPException(status_code=404, detail="Metrics file not found")

    with open(metrics_path, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    return ResponseEnvelope(data=metrics)
