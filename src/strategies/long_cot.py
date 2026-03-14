from typing import Any, Dict, List, Optional

from src.strategies.cot import CoTStrategy


class LongCoTStrategy(CoTStrategy):
    """Backward-compatible alias for CoT with reasoning_depth=deep.

    Equivalent to ``CoTStrategy(config={"reasoning_depth": "deep"})``.
    Kept so that ``load_strategy("long_cot")`` still works and existing
    experiment configs referencing ``long_cot`` are not broken.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        merged = {"reasoning_depth": "deep", **(config or {})}
        super().__init__(merged)
