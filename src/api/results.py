"""
Results and metrics API routes.

Endpoints:
- GET /results/{experiment_id}/metrics - Get experiment metrics
- GET /results/{experiment_id}/predictions - Browse predictions
- POST /results/compare - Compare multiple experiments
- GET /results/{experiment_id}/export - Export results
"""

import csv
import json
import re
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
    RAGTrace,
    RAGTraceChunk,
    ResponseEnvelope,
    UsageInfo,
)

router = APIRouter(tags=["results"])

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
            model=metrics.get("model"),
            strategy=metrics.get("strategy"),
            dataset=metrics.get("dataset"),
            total_samples=metrics.get("total_samples"),
            valid_samples=metrics.get("valid_samples"),
            evaluated_at=metrics.get("evaluated_at"),
            overall=metrics.get("overall", {}),
            by_difficulty=metrics.get("by_difficulty"),
            by_topic=metrics.get("by_topic"),
            by_category=metrics.get("by_category"),
            by_call_type=metrics.get("by_call_type"),
            by_question_type=metrics.get("by_question_type"),
            latency_stats=metrics.get("latency_stats"),
            token_stats=metrics.get("token_stats"),
            cost_estimate=metrics.get("cost_estimate"),
            option_bias=metrics.get("option_bias"),
            exact_match=metrics.get("exact_match"),
            f1_score=metrics.get("f1_score"),
            bleu=metrics.get("bleu"),
            rouge_l=metrics.get("rouge_l"),
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
        # Build RAG trace if present
        rag_trace = None
        rag_raw = pred.get("rag_context")
        if rag_raw and isinstance(rag_raw, dict) and rag_raw.get("mode"):
            chunks = [
                RAGTraceChunk(
                    chunk_id=c.get("chunk_id"),
                    text=c.get("text"),
                    score=c.get("score"),
                    topic=c.get("topic"),
                    source_qa_ids=c.get("source_qa_ids"),
                )
                for c in rag_raw.get("retrieved_chunks", [])
            ]
            rag_trace = RAGTrace(
                mode=rag_raw.get("mode"),
                query_text=rag_raw.get("query_text"),
                retrieval_latency_ms=rag_raw.get("retrieval_latency_ms"),
                retrieved_chunks=chunks,
                source_qa_ids=rag_raw.get("source_qa_ids"),
                topic=rag_raw.get("topic"),
            )
        items.append(PredictionItem(
            sample_id=pred.get("sample_id", ""),
            question=pred.get("question") or pred.get("input_prompt"),
            options=pred.get("options"),
            ground_truth=pred.get("ground_truth") or pred.get("answer") or pred.get("reference_answer"),
            parsed_answer=pred.get("parsed_answer"),
            raw_output=pred.get("raw_output"),
            correct=pred.get("correct"),
            reasoning_trace=pred.get("reasoning_trace"),
            rag_context=rag_trace,
            model=pred.get("model"),
            strategy=pred.get("strategy"),
            usage=UsageInfo(
                total_tokens=usage_data.get("total_tokens", 0),
                latency_ms=int(usage_data.get("latency_ms", 0)),
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
    format: Literal["csv", "json", "jsonl", "latex"] = Query(
        default="json", description="Export format: csv, json, jsonl, latex"
    ),
    include: Literal["predictions", "metrics", "all"] = Query(
        default="all",
        description="What to include"
    ),
) -> StreamingResponse:
    """
    Export experiment results as a downloadable file.

    Formats:
    - json: Full structured export (predictions + metrics).
    - jsonl: One prediction per line (for streaming / pandas).
    - csv: Flat table with all key fields (proper quoting via csv.writer).
    - latex: Metrics summary as a LaTeX booktabs table (for papers).
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
        lines = [json.dumps(pred, ensure_ascii=False) for pred in predictions]
        content = "\n".join(lines)
        media_type = "application/x-ndjson"
        filename = f"{experiment_id}.jsonl"

    elif format == "csv":
        if not predictions:
            raise HTTPException(status_code=400, detail="CSV export requires predictions data")

        output = StringIO()
        headers = [
            "sample_id", "question", "reference_answer", "parsed_answer", "correct",
            "model", "strategy", "difficulty",
            "latency_ms", "total_tokens", "prompt_tokens", "completion_tokens",
            "rag_mode", "rag_chunks", "reasoning_steps",
        ]
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(headers)

        for pred in predictions:
            usage = pred.get("usage") or {}
            rag_ctx = pred.get("rag_context") or {}
            trace = pred.get("reasoning_trace")
            if isinstance(trace, list):
                step_count = len(trace)
            elif isinstance(trace, str) and trace.strip():
                step_count = len(re.findall(r'^(Step|Thought|\d+[\.\)\:])', trace, re.MULTILINE)) or len([s for s in trace.split('\n\n') if s.strip()])
            else:
                step_count = 0

            writer.writerow([
                pred.get("sample_id", ""),
                str(pred.get("question", ""))[:500],
                str(pred.get("reference_answer", pred.get("ground_truth", ""))),
                str(pred.get("parsed_answer", "")),
                pred.get("correct", ""),
                pred.get("model", ""),
                pred.get("strategy", ""),
                pred.get("difficulty", ""),
                usage.get("latency_ms", ""),
                usage.get("total_tokens", ""),
                usage.get("prompt_tokens", ""),
                usage.get("completion_tokens", ""),
                rag_ctx.get("mode", ""),
                len(rag_ctx.get("retrieved_chunks", [])) if rag_ctx else "",
                step_count if step_count > 0 else "",
            ])

        content = output.getvalue()
        media_type = "text/csv; charset=utf-8"
        filename = f"{experiment_id}.csv"

    elif format == "latex":
        if metrics is None:
            raise HTTPException(status_code=400, detail="LaTeX export requires metrics data")

        overall = metrics.get("overall", {})
        model = metrics.get("model", experiment_id)
        strategy = metrics.get("strategy", "-")
        dataset = metrics.get("dataset", "-")
        total = metrics.get("total_samples", "-")

        # Build metric columns from overall dict
        metric_keys = sorted(overall.keys())
        if not metric_keys:
            metric_keys = ["(no metrics)"]

        def _tex_esc(s: str) -> str:
            return str(s).replace("_", "\\_")

        # Header row
        col_headers = ["Model", "Strategy", "Dataset", "N"] + [_tex_esc(k) for k in metric_keys]
        col_fmt = "l" * 4 + "r" * len(metric_keys)

        exp_id_tex = _tex_esc(experiment_id)
        lines = [
            "\\begin{table}[htbp]",
            "\\centering",
            f"\\caption{{Evaluation results for {exp_id_tex}}}",
            f"\\label{{tab:{experiment_id}}}",
            f"\\begin{{tabular}}{{{col_fmt}}}",
            "\\toprule",
            " & ".join(col_headers) + " \\\\",
            "\\midrule",
        ]

        # Value row
        def _fmt_val(v):
            if isinstance(v, float):
                return f"{v:.4f}" if v < 1 else f"{v:.1f}"
            return str(v)

        dataset_short = str(dataset).split("/")[-1].replace(".jsonl", "")
        vals = [
            _tex_esc(model),
            strategy,
            _tex_esc(dataset_short),
            str(total),
        ] + [_fmt_val(overall.get(k, "-")) for k in metric_keys]
        lines.append(" & ".join(vals) + " \\\\")

        lines.extend([
            "\\bottomrule",
            "\\end{tabular}",
            "\\end{table}",
        ])
        content = "\n".join(lines)
        media_type = "text/plain; charset=utf-8"
        filename = f"{experiment_id}.tex"

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

    return StreamingResponse(
        iter([content]),
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
