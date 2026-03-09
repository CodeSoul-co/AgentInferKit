"""
Prompt Loader — loads prompt configs by prompt_id from the registry.

Usage:
    from src.prompts.loader import load_prompt, render_instruction

    prompt = load_prompt("text_exam.cot")
    text = render_instruction(prompt, question="What is 2+2?", options_text="A. 3\\nB. 4")
"""

from pathlib import Path
from typing import Any, Dict, Optional

import yaml

_PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "configs" / "prompts"
_REGISTRY_PATH = _PROMPTS_DIR / "registry.yaml"

_registry_cache: Optional[Dict[str, str]] = None
_prompt_cache: Dict[str, Dict[str, Any]] = {}


def _load_registry() -> Dict[str, str]:
    """Load and cache the prompt registry mapping."""
    global _registry_cache
    if _registry_cache is not None:
        return _registry_cache
    if not _REGISTRY_PATH.exists():
        raise FileNotFoundError(f"Prompt registry not found: {_REGISTRY_PATH}")
    with open(_REGISTRY_PATH, "r", encoding="utf-8") as f:
        _registry_cache = yaml.safe_load(f) or {}
    return _registry_cache


def list_prompt_ids() -> list:
    """List all registered prompt_id keys."""
    return sorted(_load_registry().keys())


def load_prompt(prompt_id: str) -> Dict[str, Any]:
    """Load a prompt config by its prompt_id (e.g. 'text_exam.cot').

    Args:
        prompt_id: Key in the format '{task_type}.{strategy}'.

    Returns:
        Dict with keys: id, task_type, strategy, version,
        system_prompt, instruction_template, output_format.

    Raises:
        KeyError: If prompt_id is not found in the registry.
        FileNotFoundError: If the referenced YAML file does not exist.
    """
    if prompt_id in _prompt_cache:
        return _prompt_cache[prompt_id]

    registry = _load_registry()
    if prompt_id not in registry:
        available = ", ".join(sorted(registry.keys()))
        raise KeyError(
            f"Prompt ID '{prompt_id}' not found in registry. Available: {available}"
        )

    rel_path = registry[prompt_id]
    full_path = _PROMPTS_DIR / rel_path
    if not full_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {full_path}")

    with open(full_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    _prompt_cache[prompt_id] = data
    return data


def get_system_prompt(prompt_id: str) -> str:
    """Get the system prompt for a given prompt_id."""
    data = load_prompt(prompt_id)
    return (data.get("system_prompt") or "").strip()


def get_instruction_template(prompt_id: str) -> str:
    """Get the raw instruction template for a given prompt_id."""
    data = load_prompt(prompt_id)
    tpl = data.get("instruction_template")
    if not tpl:
        raise KeyError(f"No instruction_template in prompt '{prompt_id}'")
    return tpl


def get_prompt_version(prompt_id: str) -> str:
    """Get the version string for a given prompt_id."""
    data = load_prompt(prompt_id)
    return data.get("version", "1.0")


def render_instruction(prompt_id: str, **kwargs: Any) -> str:
    """Render the instruction template with variable substitution.

    Args:
        prompt_id: The prompt_id to load.
        **kwargs: Variables to substitute (e.g. question, options_text).

    Returns:
        Rendered instruction string.
    """
    tpl = get_instruction_template(prompt_id)
    return tpl.format(**kwargs)


def resolve_prompt_id(task_type: str, strategy: str) -> str:
    """Resolve a prompt_id from task_type and strategy name.

    Falls back to '{task_type}.direct' if the specific combo is not found,
    then to 'text_exam.{strategy}' as a last resort.

    Args:
        task_type: e.g. 'text_exam', 'qa', 'api_calling'
        strategy: e.g. 'cot', 'direct', 'long_cot'

    Returns:
        A valid prompt_id string.

    Raises:
        KeyError: If no suitable prompt_id can be resolved.
    """
    registry = _load_registry()

    # Exact match
    exact = f"{task_type}.{strategy}"
    if exact in registry:
        return exact

    # Fallback: task_type.direct
    fallback1 = f"{task_type}.direct"
    if fallback1 in registry:
        return fallback1

    # Fallback: text_exam.{strategy}
    fallback2 = f"text_exam.{strategy}"
    if fallback2 in registry:
        return fallback2

    available = ", ".join(sorted(registry.keys()))
    raise KeyError(
        f"Cannot resolve prompt for task_type='{task_type}', strategy='{strategy}'. "
        f"Available: {available}"
    )
