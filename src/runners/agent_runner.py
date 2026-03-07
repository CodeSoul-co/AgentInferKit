from typing import Any, Callable, Dict, List, Optional

from src.runners.base import BaseRunner


class AgentRunner(BaseRunner):
    """Runner for agent/function-calling tasks. Skeleton for phase 3 implementation."""

    def __init__(self, **kwargs: Any) -> None:
        raise NotImplementedError("AgentRunner is not yet implemented (phase 3).")

    async def run_single(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("AgentRunner.run_single() is not yet implemented (phase 3).")

    async def run_batch(
        self,
        samples: List[Dict[str, Any]],
        experiment_id: str,
        on_progress: Optional[Callable[[int, int, int], None]] = None,
    ) -> str:
        raise NotImplementedError("AgentRunner.run_batch() is not yet implemented (phase 3).")
