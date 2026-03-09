"""Prompt management module — loads prompt configs from src/prompts/."""

from src.prompts.loader import (
    get_instruction_template,
    get_prompt_version,
    get_system_prompt,
    list_prompt_ids,
    load_prompt,
    render_instruction,
    resolve_prompt_id,
)

__all__ = [
    "load_prompt",
    "render_instruction",
    "resolve_prompt_id",
    "get_system_prompt",
    "get_instruction_template",
    "get_prompt_version",
    "list_prompt_ids",
]
