import asyncio
import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from loguru import logger

from src.config import OUTPUTS_PREDICTIONS_DIR
from src.runners.base import BaseRunner
from src.utils.file_io import write_jsonl


class BatchRunner:
    """Orchestrate batch inference with concurrency control and checkpoint resume.

    Reads progress.json to skip already-completed samples, uses asyncio.Semaphore
    for bounded concurrency, and appends each result to the predictions JSONL in real time.
    """

    def __init__(
        self,
        experiment_id: str,
        model_name: str = "",
        strategy_name: str = "",
    ) -> None:
        self._experiment_id = experiment_id
        self._model_name = model_name
        self._strategy_name = strategy_name

    async def run(
        self,
        runner: BaseRunner,
        samples: List[Dict[str, Any]],
        experiment_id: str,
        concurrency: int = 5,
        on_progress: Optional[Callable[[int, int, int], None]] = None,
    ) -> str:
        """Run batch inference with checkpoint resume support.

        Args:
            runner: A BaseRunner instance (e.g. QARunner, ExamRunner).
            samples: Full list of samples to process.
            experiment_id: Experiment ID for file naming.
            concurrency: Max concurrent requests.
            on_progress: Callback fn(completed, total, failed) for SSE.

        Returns:
            Path to the predictions JSONL file.
        """
        predictions_dir = OUTPUTS_PREDICTIONS_DIR
        predictions_dir.mkdir(parents=True, exist_ok=True)
        predictions_path = predictions_dir / f"{experiment_id}.jsonl"
        progress_path = predictions_dir / f"{experiment_id}_progress.json"

        # Load checkpoint: find already-completed sample_ids
        completed_ids: Set[str] = set()
        if progress_path.exists():
            try:
                with open(progress_path, "r", encoding="utf-8") as f:
                    progress_data = json.load(f)
                completed_ids = set(progress_data.get("completed_ids", []))
                logger.info(
                    f"Resuming experiment {experiment_id}: "
                    f"{len(completed_ids)} samples already completed"
                )
            except Exception as e:
                logger.warning(f"Failed to read progress file: {e}")

        # Filter out already-completed samples
        remaining = [s for s in samples if s.get("sample_id", "") not in completed_ids]
        total = len(samples)
        completed = len(completed_ids)
        failed = 0

        if not remaining:
            logger.info(f"All {total} samples already completed for {experiment_id}")
            if on_progress:
                on_progress(total, total, 0)
            return str(predictions_path)

        logger.info(
            f"Running {len(remaining)}/{total} samples "
            f"(concurrency={concurrency})"
        )

        semaphore = asyncio.Semaphore(concurrency)
        lock = asyncio.Lock()

        async def _process(sample: Dict[str, Any]) -> None:
            nonlocal completed, failed
            async with semaphore:
                try:
                    prediction = await runner.run_single(sample)
                    # Fill in experiment-level fields
                    prediction["experiment_id"] = experiment_id
                    prediction["model"] = self._model_name
                    prediction["strategy"] = self._strategy_name

                    async with lock:
                        # Append to predictions JSONL
                        write_jsonl(str(predictions_path), [prediction], mode="a")
                        # Update completed set
                        completed_ids.add(sample.get("sample_id", ""))
                        completed += 1
                        # Write progress checkpoint
                        self._save_progress(progress_path, completed_ids, total, failed)

                except Exception as e:
                    logger.error(
                        f"Failed sample {sample.get('sample_id', '?')}: {e}"
                    )
                    async with lock:
                        failed += 1

                if on_progress:
                    on_progress(completed, total, failed)

        tasks = [_process(s) for s in remaining]
        await asyncio.gather(*tasks)

        logger.info(
            f"Batch complete: {completed}/{total} succeeded, {failed} failed"
        )
        return str(predictions_path)

    def _save_progress(
        self,
        progress_path: Path,
        completed_ids: Set[str],
        total: int,
        failed: int,
    ) -> None:
        """Write progress checkpoint to disk."""
        data = {
            "experiment_id": self._experiment_id,
            "completed_ids": sorted(completed_ids),
            "completed": len(completed_ids),
            "total": total,
            "failed": failed,
        }
        with open(progress_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
