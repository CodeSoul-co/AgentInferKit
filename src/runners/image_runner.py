from typing import Any, Callable, Dict, List, Optional

from src.runners.base import BaseRunner


class ImageRunner(BaseRunner):
    """Runner for image tasks. Skeleton for phase 2 implementation."""

    def __init__(self, **kwargs: Any) -> None:
        raise NotImplementedError("ImageRunner is not yet implemented (phase 2).")

    async def run_single(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("ImageRunner.run_single() is not yet implemented (phase 2).")

    async def run_batch(
        self,
        samples: List[Dict[str, Any]],
        experiment_id: str,
        on_progress: Optional[Callable[[int, int, int], None]] = None,
    ) -> str:
        raise NotImplementedError("ImageRunner.run_batch() is not yet implemented (phase 2).")
