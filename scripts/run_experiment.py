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
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.adapters.registry import load_adapter
from src.config import OUTPUTS_METRICS_DIR, OUTPUTS_PREDICTIONS_DIR
from src.evaluators.registry import evaluate_all
from src.runners.batch_runner import BatchRunner
from src.runners.exam_runner import ExamRunner
from src.runners.qa_runner import QARunner
from src.strategies.registry import load_strategy
from src.utils.file_io import load_config_yaml, read_jsonl, write_jsonl
from src.utils.id_gen import generate_experiment_id


async def run(config: Dict[str, Any]) -> None:
    experiment_id = config.get("experiment_id") or generate_experiment_id()
    print(f"Experiment ID: {experiment_id}")

    # Load model adapter
    model_config = config.get("model", {})
    adapter = load_adapter(model_config)
    model_name = model_config.get("model", model_config.get("provider", "unknown"))
    print(f"Model: {model_name}")

    # Load strategy
    strategy_name = config.get("strategy", "direct")
    strategy_config = config.get("strategy_config", {})
    strategy = load_strategy(strategy_name, strategy_config)
    print(f"Strategy: {strategy_name}")

    # Load dataset
    dataset_path = config.get("dataset_path", "")
    samples = read_jsonl(dataset_path)
    print(f"Dataset: {dataset_path} ({len(samples)} samples)")

    # Determine runner type from task_type of first sample
    task_type = samples[0].get("task_type", "text_qa") if samples else "text_qa"
    rag_config = config.get("rag", {})

    if task_type in ("text_exam", "image_mcq"):
        runner = ExamRunner(adapter, strategy, rag_config=rag_config)
    else:
        runner = QARunner(adapter, strategy, rag_config=rag_config)

    # Merge reference fields into samples for evaluation later
    # (samples already have them from the dataset)

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

        evaluator_kwargs = config.get("evaluator_kwargs", {})
        results = evaluate_all(predictions, evaluator_names, evaluator_kwargs)

        # Write metrics
        metrics_dir = OUTPUTS_METRICS_DIR
        metrics_dir.mkdir(parents=True, exist_ok=True)
        metrics_path = metrics_dir / f"{experiment_id}.json"
        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"Metrics: {metrics_path}")

        for name, result in results.items():
            # Print summary (skip details)
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
