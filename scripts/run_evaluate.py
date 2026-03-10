"""Script: Run evaluation only — reads predictions.jsonl, outputs metrics.json.

Usage:
    python scripts/run_evaluate.py --predictions outputs/predictions/exp_001.jsonl \
                                   --dataset data/benchmark/text_exam/demo.jsonl \
                                   --evaluators choice_accuracy latency_stats \
                                   --group-by difficulty metadata.topic

    python scripts/run_evaluate.py --config configs/experiments/my_experiment.yaml \
                                   --predictions outputs/predictions/exp_001.jsonl

When --config is provided, evaluators / group-by / dataset are read from the config
unless overridden by explicit CLI flags.
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import OUTPUTS_METRICS_DIR
from src.evaluators.registry import evaluate_all
from src.evaluators.group_stats import multi_group_stats
from src.utils.file_io import load_config_yaml, read_jsonl


def _build_overall(
    metric_results: Dict[str, Any],
    predictions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Build the 'overall' summary block from metric results."""
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

    if "cost_estimate" in metric_results:
        overall["total_cost_usd"] = metric_results["cost_estimate"].get("estimated_cost_usd", 0.0)

    return overall


def run_evaluate(
    predictions_path: str,
    dataset_path: str,
    evaluator_names: List[str],
    group_by: List[str],
    experiment_id: str = "",
    output_path: str = "",
    evaluator_kwargs: Dict[str, Any] = None,
) -> str:
    """Run evaluation and return the metrics file path.

    Args:
        predictions_path: Path to predictions JSONL.
        dataset_path: Path to original dataset JSONL (for reference answers).
        evaluator_names: List of evaluator metric names.
        group_by: Grouping dimensions.
        experiment_id: Optional experiment ID for the metrics file name.
        output_path: Optional explicit output path for the metrics JSON.
        evaluator_kwargs: Optional per-evaluator kwargs dict.

    Returns:
        Path to the metrics JSON file.
    """
    predictions = read_jsonl(predictions_path)
    samples = read_jsonl(dataset_path) if dataset_path else []
    print(f"Predictions: {predictions_path} ({len(predictions)} items)")
    if samples:
        print(f"Dataset: {dataset_path} ({len(samples)} samples)")

    # Merge reference data from samples into predictions
    if samples:
        sample_map = {s["sample_id"]: s for s in samples}
        for pred in predictions:
            sid = pred.get("sample_id", "")
            if sid in sample_map:
                orig = sample_map[sid]
                pred.setdefault("answer", orig.get("answer", ""))
                pred.setdefault("reference_answer", orig.get("reference_answer", ""))
                pred.setdefault("difficulty", orig.get("difficulty", ""))
                pred.setdefault("metadata", orig.get("metadata", {}))

    if not evaluator_names:
        print("No evaluators specified. Nothing to do.")
        return ""

    # Evaluate
    metric_results = evaluate_all(predictions, evaluator_names, evaluator_kwargs or {})
    overall = _build_overall(metric_results, predictions)
    valid_samples = sum(1 for p in predictions if not p.get("error"))

    # Group stats
    grouped = multi_group_stats(predictions, samples, group_by) if group_by and samples else {}

    # Derive experiment_id from predictions path if not given
    if not experiment_id:
        experiment_id = Path(predictions_path).stem

    # Build metrics output
    model_name = predictions[0].get("model", "") if predictions else ""
    strategy_name = predictions[0].get("strategy", "") if predictions else ""

    metrics_output: Dict[str, Any] = {
        "experiment_id": experiment_id,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "model": model_name,
        "strategy": strategy_name,
        "dataset": dataset_path,
        "total_samples": len(predictions),
        "valid_samples": valid_samples,
        "overall": overall,
    }

    # Merge grouped stats
    metrics_output.update(grouped)

    # Merge per-metric details
    for name, result in metric_results.items():
        if name in ("choice_accuracy", "exact_match", "f1_score",
                     "latency_stats", "token_stats", "cost_estimate"):
            continue
        if name == "option_bias":
            metrics_output["option_bias"] = result.get("distribution")
        elif name in ("tool_selection_accuracy", "parameter_accuracy",
                      "end_to_end_success_rate", "invalid_call_rate", "avg_tool_calls"):
            metrics_output.setdefault("agent_metrics", {})[name] = result
        elif name in ("retrieval_hit_rate", "context_relevance"):
            metrics_output.setdefault("rag_metrics", {})[name] = result
        else:
            metrics_output[name] = result

    # Write metrics
    if not output_path:
        metrics_dir = OUTPUTS_METRICS_DIR
        metrics_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(metrics_dir / f"{experiment_id}.json")
    else:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metrics_output, f, ensure_ascii=False, indent=2)
    print(f"Metrics: {output_path}")

    # Print summary
    print(f"  overall: {overall}")
    for dim, groups in grouped.items():
        print(f"  {dim}:")
        for gkey, gval in groups.items():
            print(f"    {gkey}: acc={gval['accuracy']}, count={gval['count']}")

    for name, result in metric_results.items():
        if name not in ("choice_accuracy", "exact_match", "f1_score",
                         "latency_stats", "token_stats", "cost_estimate", "option_bias"):
            summary = {k: v for k, v in result.items() if k != "details"}
            print(f"  {name}: {summary}")

    print("Done.")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run evaluation on predictions (no inference).")
    parser.add_argument("--predictions", required=True, help="Path to predictions JSONL file.")
    parser.add_argument("--dataset", default="", help="Path to original dataset JSONL (for reference answers).")
    parser.add_argument("--evaluators", nargs="*", default=None, help="Evaluator metric names.")
    parser.add_argument("--group-by", nargs="*", default=None, help="Grouping dimensions.")
    parser.add_argument("--output", default="", help="Optional explicit output path for metrics JSON.")
    parser.add_argument("--config", default="", help="Optional experiment config YAML (for evaluators/dataset defaults).")
    args = parser.parse_args()

    # Load defaults from config if provided
    evaluator_names = args.evaluators or []
    group_by = args.group_by or []
    dataset_path = args.dataset
    experiment_id = ""
    evaluator_kwargs = {}

    if args.config:
        config = load_config_yaml(args.config)
        if not evaluator_names:
            evaluator_names = config.get("evaluators", [])
        if not group_by:
            group_by = config.get("group_by", ["difficulty", "metadata.topic"])
        if not dataset_path:
            dataset_path = config.get("dataset_path", "")
        experiment_id = config.get("experiment_id", "")
        evaluator_kwargs = config.get("evaluator_kwargs", {})

    if not evaluator_names:
        print("ERROR: No evaluators specified. Use --evaluators or --config.", file=sys.stderr)
        sys.exit(1)

    run_evaluate(
        predictions_path=args.predictions,
        dataset_path=dataset_path,
        evaluator_names=evaluator_names,
        group_by=group_by,
        experiment_id=experiment_id,
        output_path=args.output,
        evaluator_kwargs=evaluator_kwargs,
    )


if __name__ == "__main__":
    main()
