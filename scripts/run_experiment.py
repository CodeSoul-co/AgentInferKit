"""Script: Run a full experiment from config YAML.

Usage:
    python scripts/run_experiment.py --config configs/experiments/my_experiment.yaml

The experiment config should contain:
    experiment_id, model (provider + params), strategy, dataset_path,
    concurrency, rag (optional), evaluators list.
"""
import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.adapters.registry import load_adapter
from src.config import OUTPUTS_METRICS_DIR, OUTPUTS_PREDICTIONS_DIR
from src.evaluators.registry import evaluate_all
from src.evaluators.group_stats import multi_group_stats
from src.runners.agent_runner import AgentRunner
from src.runners.batch_runner import BatchRunner
from src.runners.exam_runner import ExamRunner
from src.runners.qa_runner import QARunner
from src.strategies.registry import load_strategy
from src.utils.file_io import load_config_yaml, read_jsonl, write_jsonl
from src.utils.id_gen import generate_experiment_id


def _build_overall(
    metric_results: Dict[str, Any],
    predictions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Build the 'overall' summary block from metric results."""
    overall: Dict[str, Any] = {}

    # Accuracy: from choice_accuracy or exact_match
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


async def run(config: Dict[str, Any]) -> None:
    experiment_id = config.get("experiment_id") or generate_experiment_id()
    print(f"Experiment ID: {experiment_id}")

    # Load model adapter
    model_config = config.get("model", {})
    adapter = load_adapter(model_config)
    model_name = model_config.get("model", model_config.get("provider", "unknown"))
    print(f"Model: {model_name}")

    # Load strategy (pass prompt_id into strategy config if present)
    strategy_name = config.get("strategy", "direct")
    strategy_config = config.get("strategy_config", {})
    prompt_id = config.get("prompt_id")
    if prompt_id:
        strategy_config["prompt_id"] = prompt_id
    strategy = load_strategy(strategy_name, strategy_config)
    print(f"Strategy: {strategy_name}")
    if prompt_id:
        print(f"Prompt ID: {prompt_id}")

    # Load dataset
    dataset_path = config.get("dataset_path", "")
    samples = read_jsonl(dataset_path)
    print(f"Dataset: {dataset_path} ({len(samples)} samples)")

    # Determine runner type from task_type of first sample
    task_type = samples[0].get("task_type", "text_qa") if samples else "text_qa"
    rag_config = config.get("rag", {})

    if task_type == "api_calling":
        runner = AgentRunner(adapter, strategy, model_config=model_config, rag_config=rag_config)
    elif task_type in ("text_exam", "image_mcq"):
        runner = ExamRunner(adapter, strategy, rag_config=rag_config)
    else:
        runner = QARunner(adapter, strategy, rag_config=rag_config)

    # Run batch
    concurrency = config.get("concurrency", 5)
    batch_runner = BatchRunner(experiment_id, model_name=model_name, strategy_name=strategy_name)

    def on_progress(completed: int, total: int, failed: int) -> None:
        print(f"\r  Progress: {completed}/{total} (failed={failed})", end="", flush=True)

    predictions_path = await batch_runner.run(
        runner, samples, experiment_id, concurrency=concurrency, on_progress=on_progress
    )
    print(f"\nPredictions: {predictions_path}")

    # Evaluate
    evaluator_names = config.get("evaluators", [])
    if evaluator_names:
        predictions = read_jsonl(predictions_path)

        # Merge reference data from samples into predictions for evaluation
        sample_map = {s["sample_id"]: s for s in samples}
        for pred in predictions:
            sid = pred.get("sample_id", "")
            if sid in sample_map:
                orig = sample_map[sid]
                pred.setdefault("answer", orig.get("answer", ""))
                pred.setdefault("reference_answer", orig.get("reference_answer", ""))
                pred.setdefault("difficulty", orig.get("difficulty", ""))
                pred.setdefault("metadata", orig.get("metadata", {}))

        evaluator_kwargs = config.get("evaluator_kwargs", {})
        metric_results = evaluate_all(predictions, evaluator_names, evaluator_kwargs)

        # Build overall summary
        overall = _build_overall(metric_results, predictions)
        valid_samples = sum(1 for p in predictions if not p.get("error"))

        # Group stats
        group_by = config.get("group_by", ["difficulty", "metadata.topic"])
        grouped = multi_group_stats(predictions, samples, group_by)

        # Build standardized metrics output (FORMAT_AND_METRICS.md section 2.2)
        metrics_output: Dict[str, Any] = {
            "experiment_id": experiment_id,
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "model": model_name,
            "strategy": strategy_name,
            "dataset": dataset_path,
            "total_samples": len(samples),
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
        metrics_dir = OUTPUTS_METRICS_DIR
        metrics_dir.mkdir(parents=True, exist_ok=True)
        metrics_path = metrics_dir / f"{experiment_id}.json"
        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(metrics_output, f, ensure_ascii=False, indent=2)
        print(f"Metrics: {metrics_path}")

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


def main() -> None:
    parser = argparse.ArgumentParser(description="Run inference experiment from config.")
    parser.add_argument("--config", required=True, help="Path to experiment config YAML.")
    args = parser.parse_args()

    config = load_config_yaml(args.config)
    asyncio.run(run(config))


if __name__ == "__main__":
    main()
