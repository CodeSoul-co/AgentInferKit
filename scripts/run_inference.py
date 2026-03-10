"""Script: Run inference only — outputs predictions.jsonl.

Usage:
    python scripts/run_inference.py --config configs/experiments/my_experiment.yaml
    python scripts/run_inference.py --config ... --output outputs/predictions/custom.jsonl

The experiment config should contain:
    experiment_id, model (provider + params), strategy, dataset_path, concurrency.
Evaluation is NOT run here; use run_evaluate.py separately.
"""
import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.adapters.registry import load_adapter
from src.config import OUTPUTS_PREDICTIONS_DIR
from src.runners.agent_runner import AgentRunner
from src.runners.batch_runner import BatchRunner
from src.runners.exam_runner import ExamRunner
from src.runners.qa_runner import QARunner
from src.strategies.registry import load_strategy
from src.utils.file_io import load_config_yaml, read_jsonl
from src.utils.id_gen import generate_experiment_id


async def run_inference(config: Dict[str, Any], output_path: str = "") -> str:
    """Run inference and return the predictions file path.

    Args:
        config: Experiment config dict.
        output_path: Optional explicit output file path.

    Returns:
        Path to the predictions JSONL file.
    """
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

    # Determine runner
    task_type = samples[0].get("task_type", "text_qa") if samples else "text_qa"
    rag_config = config.get("rag", {})

    if task_type == "api_calling":
        runner = AgentRunner(adapter, strategy, model_config=model_config, rag_config=rag_config)
    elif task_type in ("text_exam", "image_mcq"):
        runner = ExamRunner(adapter, strategy, model_config=model_config, rag_config=rag_config)
    else:
        runner = QARunner(adapter, strategy, model_config=model_config, rag_config=rag_config)

    # Run batch
    concurrency = config.get("concurrency", 5)
    batch_runner = BatchRunner(experiment_id, model_name=model_name, strategy_name=strategy_name)

    def on_progress(completed: int, total: int, failed: int) -> None:
        print(f"\r  Progress: {completed}/{total} (failed={failed})", end="", flush=True)

    predictions_path = await batch_runner.run(
        runner, samples, experiment_id, concurrency=concurrency, on_progress=on_progress
    )

    # If explicit output_path requested, copy there
    if output_path and output_path != predictions_path:
        import shutil
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(predictions_path, output_path)
        predictions_path = output_path

    print(f"\nPredictions: {predictions_path}")
    print("Done. Run scripts/run_evaluate.py to compute metrics.")
    return predictions_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run inference only (no evaluation).")
    parser.add_argument("--config", required=True, help="Path to experiment config YAML.")
    parser.add_argument("--output", default="", help="Optional explicit output path for predictions JSONL.")
    args = parser.parse_args()

    config = load_config_yaml(args.config)
    asyncio.run(run_inference(config, output_path=args.output))


if __name__ == "__main__":
    main()
