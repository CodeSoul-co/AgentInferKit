from typing import Any, Dict, List, Optional

from src.api.schemas import Message
from src.strategies.base import BaseStrategy


class SelfRefineStrategy(BaseStrategy):
    """Self-Refine strategy using LangChain LLMChain for multi-round refinement.

    Reads config from configs/strategies/self_refine.yaml.
    Three-phase iterative loop:
      1. Generate an initial answer.
      2. Critique the answer (feedback).
      3. Refine the answer based on feedback.
    The caller drives the loop; this class provides prompt builders.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__("self_refine", config)
        refine_cfg = self._yaml_cfg.get("refine_config", {})
        self._max_rounds = self._runtime_cfg.get("max_rounds", refine_cfg.get("max_rounds", 3))

    @property
    def max_rounds(self) -> int:
        return self._max_rounds

    def build_prompt(self, sample: Dict[str, Any], **kwargs: Any) -> List[Message]:
        """Build the initial-generation prompt."""
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

    def build_feedback_prompt(
        self, sample: Dict[str, Any], previous_answer: str
    ) -> List[Message]:
        """Build the critique/feedback prompt."""
        question = sample.get("question", "")
        content = self.render_prompt("feedback", question=question, previous_answer=previous_answer)
        return [Message(role="user", content=content.strip())]

    def build_refine_prompt(
        self, sample: Dict[str, Any], previous_answer: str, feedback: str
    ) -> List[Message]:
        """Build the refinement prompt."""
        task_type = sample.get("task_type", "text_qa")
        question = sample.get("question", "")

        if task_type in ("text_exam", "image_mcq"):
            content = self.render_prompt(
                "refine_exam", question=question,
                previous_answer=previous_answer, feedback=feedback,
            )
        else:
            content = self.render_prompt(
                "refine_qa", question=question,
                previous_answer=previous_answer, feedback=feedback,
            )

        return [Message(role="user", content=content.strip())]
