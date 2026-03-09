from typing import Any, Dict, List, Optional

from src.api.schemas import Message
from src.strategies.base import BaseStrategy


class LongCoTStrategy(BaseStrategy):
    """Long Chain-of-Thought strategy.

    Reads prompt templates from configs/strategies/long_cot.yaml.
    Similar to CoT but uses a stronger system prompt for extended reasoning.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__("long_cot", config)

    def build_prompt(self, sample: Dict[str, Any], **kwargs: Any) -> List[Message]:
        task_type = sample.get("task_type", "text_qa")

        prompt_id = self.resolve_prompt(task_type)
        if prompt_id:
            self._resolved_prompt_id = prompt_id
            return self.build_messages_from_prompt_id(prompt_id, **self.build_template_vars(sample))

        # Fallback to legacy strategy YAML
        question = sample.get("question", "")
        system = self._prompts.get("system", "")
        messages: List[Message] = []
        if system and system.strip():
            messages.append(Message(role="system", content=system.strip()))

        if task_type in ("text_exam", "image_mcq"):
            options = sample.get("options", {})
            options_text = "\n".join(f"{k}. {v}" for k, v in sorted(options.items()))
            user_content = self.render_prompt("user_exam", question=question, options_text=options_text)
        else:
            user_content = self.render_prompt("user_qa", question=question)

        messages.append(Message(role="user", content=user_content.strip()))
        return messages
