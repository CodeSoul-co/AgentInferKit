import importlib
import inspect
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.strategies.base import BaseStrategy, _CONFIGS_DIR


# Strategy name -> class mapping, populated by _scan_strategies()
_STRATEGY_MAP: Dict[str, type] = {}


def _scan_strategies() -> None:
    """Dynamically scan the strategies package and register all BaseStrategy subclasses.

    Only registers strategies that have a matching YAML config in configs/strategies/.
    Convention: each .py file in src/strategies/ (except base.py and registry.py)
    maps to a strategy key equal to the file stem.
    """
    if _STRATEGY_MAP:
        return

    strategies_dir = Path(__file__).parent
    for py_file in sorted(strategies_dir.glob("*.py")):
        if py_file.name in ("__init__.py", "base.py", "registry.py"):
            continue
        module_name = f"src.strategies.{py_file.stem}"
        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue

        for _name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, BaseStrategy) and obj is not BaseStrategy:
                _STRATEGY_MAP[py_file.stem] = obj
                break


def load_strategy(name: str, config: Optional[Dict[str, Any]] = None) -> BaseStrategy:
    """Load a strategy by name and optional config.

    Args:
        name: Strategy key (e.g. 'direct', 'cot', 'long_cot').
        config: Optional config dict passed to the strategy constructor.

    Returns:
        An instance of the corresponding BaseStrategy subclass.

    Raises:
        ValueError: If the strategy name is unknown.
    """
    _scan_strategies()

    if name not in _STRATEGY_MAP:
        available = ", ".join(sorted(_STRATEGY_MAP.keys()))
        raise ValueError(f"Unknown strategy '{name}'. Available: {available}")

    strategy_cls = _STRATEGY_MAP[name]
    return strategy_cls(config=config or {})


def list_strategies() -> List[str]:
    """List all available strategy names."""
    _scan_strategies()
    return sorted(_STRATEGY_MAP.keys())
