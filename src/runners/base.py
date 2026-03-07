from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional


class BaseRunner(ABC):
    """Abstract base class for all experiment runners."""

    @abstractmethod
    async def run_single(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """Run inference on a single sample.

        Args:
            sample: A data sample dict (see SCHEMA.md).

        Returns:
            A prediction dict conforming to SCHEMA.md section 5.
        """
        ...

    @abstractmethod
    async def run_batch(
        self,
        samples: List[Dict[str, Any]],
        experiment_id: str,
        on_progress: Optional[Callable[[int, int, int], None]] = None,
    ) -> str:
        """Run inference on a batch of samples.

        Args:
            samples: List of sample dicts.
            experiment_id: Unique experiment identifier.
            on_progress: Optional callback fn(completed, total, failed) for SSE.

        Returns:
            Path to the predictions JSONL file.
        """
        ...
