from typing import Any, Dict, List, Optional

from src.api.schemas import Message
from src.strategies.base import BaseStrategy


class DirectStrategy(BaseStrategy):
    """Direct prompting strategy using LangChain LLMChain.

    Reads prompt templates from configs/strategies/direct.yaml.
    No chain-of-thought; asks the question as-is.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__("direct", config)

    def build_prompt(self, sample: Dict[str, Any], **kwargs: Any) -> List[Message]:
        task_type = sample.get("task_type", "text_qa")
        question = sample.get("question", "")

        prompt_id = self.resolve_prompt(task_type)
        if prompt_id:
            self._resolved_prompt_id = prompt_id
            return self.build_messages_from_prompt_id(prompt_id, **self.build_template_vars(sample))

        # Fallback to legacy strategy YAML
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

    def parse_output(self, raw_output: str, sample: Dict[str, Any]) -> Dict[str, Any]:
        task_type = sample.get("task_type", "text_qa")
        return {
            "parsed_answer": self._extract_answer(raw_output, task_type),
            "reasoning_trace": None,
        }
