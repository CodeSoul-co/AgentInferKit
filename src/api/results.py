"""
Results and metrics API routes.

Endpoints:
- GET /results/{experiment_id}/metrics - Get experiment metrics
- GET /results/{experiment_id}/predictions - Browse predictions
- POST /results/compare - Compare multiple experiments
- GET /results/{experiment_id}/export - Export results
"""

import json
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from .schemas import (
    CompareRequest,
    CompareResponse,
    MetricsResponse,
    PredictionItem,
    PredictionListResponse,
    ResponseEnvelope,
    UsageInfo,
)

router = APIRouter(prefix="/results", tags=["results"])

OUTPUTS_DIR = Path("outputs")
PREDICTIONS_DIR = OUTPUTS_DIR / "predictions"
METRICS_DIR = OUTPUTS_DIR / "metrics"


experiments_store: Dict[str, Dict[str, Any]] = {}
predictions_store: Dict[str, List[Dict[str, Any]]] = {}
metrics_store: Dict[str, Dict[str, Any]] = {}


def _load_predictions(experiment_id: str) -> List[Dict[str, Any]]:
    """Load predictions from file or cache."""
    if experiment_id in predictions_store:
        return predictions_store[experiment_id]
    
    pred_file = PREDICTIONS_DIR / f"{experiment_id}.jsonl"
    if not pred_file.exists():
        return []
    
    predictions = []
    with open(pred_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                predictions.append(json.loads(line))
    
    predictions_store[experiment_id] = predictions
    return predictions


def _load_metrics(experiment_id: str) -> Optional[Dict[str, Any]]:
    """Load metrics from file or cache."""
    if experiment_id in metrics_store:
        return metrics_store[experiment_id]
    
    metrics_file = METRICS_DIR / f"{experiment_id}.json"
    if not metrics_file.exists():
        return None
    
    with open(metrics_file, "r", encoding="utf-8") as f:
        metrics = json.load(f)
    
    metrics_store[experiment_id] = metrics
    return metrics


@router.get(
    "/{experiment_id}/metrics",
    response_model=ResponseEnvelope[MetricsResponse],
    summary="Get experiment metrics",
)
async def get_metrics(
    experiment_id: str,
) -> ResponseEnvelope[MetricsResponse]:
    """
    Get evaluation metrics for an experiment.
    
    Returns overall metrics and optionally grouped metrics by difficulty/topic.
    """
    metrics = _load_metrics(experiment_id)
    
    if metrics is None:
        raise HTTPException(
            status_code=404,
            detail=f"Metrics for experiment {experiment_id} not found"
        )
    
    return ResponseEnvelope(
        code=0,
        message="ok",
        data=MetricsResponse(
            experiment_id=experiment_id,
            overall=metrics.get("overall", {}),
            by_difficulty=metrics.get("by_difficulty"),
            by_topic=metrics.get("by_topic"),
        )
    )


@router.get(
    "/{experiment_id}/predictions",
    response_model=ResponseEnvelope[PredictionListResponse],
    summary="Browse predictions",
)
async def get_predictions(
    experiment_id: str,
    offset: int = Query(default=0, ge=0, description="Offset"),
    limit: int = Query(default=20, ge=1, le=100, description="Number of items"),
    correct: Optional[bool] = Query(default=None, description="Filter by correctness"),
    difficulty: Optional[str] = Query(default=None, description="Filter by difficulty"),
    has_error: Optional[bool] = Query(default=None, description="Filter by error status"),
) -> ResponseEnvelope[PredictionListResponse]:
    """
    Browse prediction results with pagination and filtering.
    """
    predictions = _load_predictions(experiment_id)
    
    if not predictions:
        raise HTTPException(
            status_code=404,
            detail=f"Predictions for experiment {experiment_id} not found"
        )
    
    filtered = predictions
    
    if correct is not None:
        filtered = [p for p in filtered if p.get("correct") == correct]
    
    if difficulty is not None:
        filtered = [p for p in filtered if p.get("difficulty") == difficulty]
    
    if has_error is not None:
        if has_error:
            filtered = [p for p in filtered if p.get("error") is not None]
        else:
            filtered = [p for p in filtered if p.get("error") is None]
    
    total = len(filtered)
    paginated = filtered[offset:offset + limit]
    
    items = []
    for pred in paginated:
        usage_data = pred.get("usage", {})
        items.append(PredictionItem(
            sample_id=pred.get("sample_id", ""),
            question=pred.get("question", ""),
            options=pred.get("options"),
            ground_truth=pred.get("ground_truth", ""),
            parsed_answer=pred.get("parsed_answer"),
            correct=pred.get("correct", False),
            reasoning_trace=pred.get("reasoning_trace"),
            usage=UsageInfo(
                total_tokens=usage_data.get("total_tokens", 0),
                latency_ms=usage_data.get("latency_ms", 0),
            ),
        ))
    
    return ResponseEnvelope(
        code=0,
        message="ok",
        data=PredictionListResponse(
            total=total,
            offset=offset,
            limit=limit,
            items=items,
        )
    )


@router.post(
    "/compare",
    response_model=ResponseEnvelope[CompareResponse],
    summary="Compare multiple experiments",
)
async def compare_experiments(
    request: CompareRequest,
) -> ResponseEnvelope[CompareResponse]:
    """
    Compare metrics across multiple experiments.
    
    Returns a table with columns for each metric and rows for each experiment.
    """
    columns = ["experiment_id", "name"] + request.metrics
    rows: List[List[Any]] = []
    by_group: Dict[str, List[List[Any]]] = {}
    
    for exp_id in request.experiment_ids:
        metrics = _load_metrics(exp_id)
        
        if metrics is None:
            row = [exp_id, exp_id] + [None] * len(request.metrics)
        else:
            overall = metrics.get("overall", {})
            row = [exp_id, metrics.get("name", exp_id)]
            for metric in request.metrics:
                row.append(overall.get(metric))
            
            if request.group_by:
                group_key = f"by_{request.group_by}"
                group_data = metrics.get(group_key, [])
                
                for group in group_data:
                    group_name = group.get("group_name", "unknown")
                    if group_name not in by_group:
                        by_group[group_name] = []
                    
                    group_row = [exp_id, metrics.get("name", exp_id)]
                    for metric in request.metrics:
                        group_row.append(group.get(metric))
                    by_group[group_name].append(group_row)
        
        rows.append(row)
    
    return ResponseEnvelope(
        code=0,
        message="ok",
        data=CompareResponse(
            columns=columns,
            rows=rows,
            by_group=by_group if by_group else None,
        )
    )


@router.get(
    "/{experiment_id}/export",
    summary="Export results",
)
async def export_results(
    experiment_id: str,
    format: Literal["csv", "json", "jsonl"] = Query(..., description="Export format"),
    include: Literal["predictions", "metrics", "all"] = Query(
        default="all",
        description="What to include"
    ),
) -> StreamingResponse:
    """
    Export experiment results as a downloadable file.
    """
    predictions = _load_predictions(experiment_id) if include in ["predictions", "all"] else []
    metrics = _load_metrics(experiment_id) if include in ["metrics", "all"] else None
    
    if not predictions and metrics is None:
        raise HTTPException(
            status_code=404,
            detail=f"No data found for experiment {experiment_id}"
        )
    
    if format == "json":
        content = json.dumps({
            "experiment_id": experiment_id,
            "predictions": predictions if include in ["predictions", "all"] else None,
            "metrics": metrics if include in ["metrics", "all"] else None,
        }, ensure_ascii=False, indent=2)
        media_type = "application/json"
        filename = f"{experiment_id}.json"
    
    elif format == "jsonl":
        lines = []
        for pred in predictions:
            lines.append(json.dumps(pred, ensure_ascii=False))
        content = "\n".join(lines)
        media_type = "application/x-ndjson"
        filename = f"{experiment_id}.jsonl"
    
    elif format == "csv":
        if not predictions:
            raise HTTPException(
                status_code=400,
                detail="CSV export requires predictions data"
            )
        
        output = StringIO()
        
        if predictions:
            headers = ["sample_id", "question", "ground_truth", "parsed_answer", "correct"]
            output.write(",".join(headers) + "\n")
            
            for pred in predictions:
                row = [
                    str(pred.get("sample_id", "")),
                    str(pred.get("question", "")).replace(",", ";").replace("\n", " ")[:100],
                    str(pred.get("ground_truth", "")),
                    str(pred.get("parsed_answer", "")),
                    str(pred.get("correct", "")),
                ]
                output.write(",".join(row) + "\n")
        
        content = output.getvalue()
        media_type = "text/csv"
        filename = f"{experiment_id}.csv"
    
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
    
    return StreamingResponse(
        iter([content]),
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
