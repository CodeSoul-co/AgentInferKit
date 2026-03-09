"""
Prompt registry — loads YAML templates and renders them with variable substitution.

Usage:
    from src.prompts import get_prompt

    text = get_prompt("cot", "user_exam", question="What is 2+3?", options_text="A. 4\\nB. 5")
"""

from pathlib import Path
from typing import Any, Dict, Optional

import yaml

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_cache: Dict[str, Dict[str, Any]] = {}


def _load_template(strategy: str) -> Dict[str, Any]:
    """Load and cache a strategy's prompt template YAML."""
    if strategy in _cache:
        return _cache[strategy]

    path = _TEMPLATES_DIR / f"{strategy}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Prompt template not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    _cache[strategy] = data
    return data


def get_prompt(strategy: str, key: str, **kwargs: Any) -> str:
    """Get a rendered prompt string.

    Args:
        strategy: Strategy name (e.g. 'cot', 'direct', 'react').
        key: Prompt key within that strategy's template (e.g. 'system', 'user_exam', 'user_qa').
        **kwargs: Variables to substitute into the template (e.g. question, options_text).

    Returns:
        The rendered prompt string.
    """
    data = _load_template(strategy)
    prompts = data.get("prompts", {})
    template = prompts.get(key)
    if template is None:
        raise KeyError(f"Prompt key '{key}' not found in '{strategy}.yaml'. Available: {list(prompts.keys())}")

    return template.format(**kwargs)


def list_strategies() -> list:
    """List all available strategy templates."""
    return sorted(p.stem for p in _TEMPLATES_DIR.glob("*.yaml"))


def list_keys(strategy: str) -> list:
    """List all prompt keys for a given strategy."""
    data = _load_template(strategy)
    return list(data.get("prompts", {}).keys())


class PromptRegistry:
    """Object-oriented wrapper around prompt template access."""

    def __init__(self, strategy: str) -> None:
        self._strategy = strategy
        self._data = _load_template(strategy)

    @property
    def metadata(self) -> Dict[str, Any]:
        """Return template metadata (name, description, version)."""
        return {
            k: self._data.get(k)
            for k in ("name", "description", "version")
            if k in self._data
        }

    def get(self, key: str, **kwargs: Any) -> str:
        """Get a rendered prompt by key."""
        return get_prompt(self._strategy, key, **kwargs)

    def keys(self) -> list:
        """List available prompt keys."""
        return list(self._data.get("prompts", {}).keys())

    def raw(self, key: str) -> str:
        """Get the raw template string (without rendering)."""
        prompts = self._data.get("prompts", {})
        if key not in prompts:
            raise KeyError(f"Prompt key '{key}' not found. Available: {list(prompts.keys())}")
        return prompts[key]
