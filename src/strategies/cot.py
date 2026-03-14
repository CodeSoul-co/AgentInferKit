from typing import Any, Dict, List, Optional

from src.api.schemas import Message
from src.strategies.base import BaseStrategy


class CoTStrategy(BaseStrategy):
    """Chain-of-Thought prompting strategy.

    Supports two reasoning depths via ``cot_config.reasoning_depth``:
      - **normal**: standard CoT ("think step by step").
      - **deep**: extended reasoning formerly called ``long_cot``
        ("break into sub-problems, verify intermediate results").

    Loads prompts from src/prompts/ registry by prompt_id.
    Falls back to configs/strategies/cot.yaml if no registry entry.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__("cot", config)
        cot_cfg = self._yaml_cfg.get("cot_config", {})
        self._reasoning_depth = self._runtime_cfg.get(
            "reasoning_depth", cot_cfg.get("reasoning_depth", "normal")
        )
        # When depth=deep, swap in deep_prompts over the default prompts
        if self._reasoning_depth == "deep":
            deep = self._yaml_cfg.get("deep_prompts", {})
            if deep:
                self._prompts = {**self._prompts, **deep}

    @property
    def reasoning_depth(self) -> str:
        return self._reasoning_depth

    def resolve_prompt(self, task_type: str) -> str:
        """Resolve prompt_id, trying long_cot registry entry for deep mode."""
        if self._explicit_prompt_id:
            return self._explicit_prompt_id
        # For deep mode, try task_type.long_cot first, then task_type.cot
        if self._reasoning_depth == "deep":
            try:
                from src.prompts.loader import resolve_prompt_id
                return resolve_prompt_id(task_type, "long_cot")
            except KeyError:
                pass
        return super().resolve_prompt(task_type)

    def build_prompt(self, sample: Dict[str, Any], **kwargs: Any) -> List[Message]:
        task_type = sample.get("task_type", "text_qa")
        question = sample.get("question", "")

        prompt_id = self.resolve_prompt(task_type)
        if prompt_id:
            tpl_vars = self.build_template_vars(sample)
            self._resolved_prompt_id = prompt_id
            return self.build_messages_from_prompt_id(prompt_id, **tpl_vars)

        # Fallback to legacy strategy YAML (uses deep_prompts if depth=deep)
        system = self._prompts.get("system", "")
        if task_type in ("text_exam", "image_mcq"):
            options = sample.get("options", {})
            options_text = "\n".join(f"{k}. {v}" for k, v in sorted(options.items()))
            user_content = self.render_prompt("user_exam", question=question, options_text=options_text)
        elif task_type == "text_qa":
            user_content = self.render_prompt("user_qa", question=question)
        else:
            user_goal = sample.get("user_goal", question)
            user_content = self.render_prompt("user_default", user_goal=user_goal)

        messages: List[Message] = []
        if system and system.strip():
            messages.append(Message(role="system", content=system.strip()))
        messages.append(Message(role="user", content=user_content.strip()))
        return messages

