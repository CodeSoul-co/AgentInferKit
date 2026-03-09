import re
from typing import Any, Dict, List, Optional

from src.api.schemas import Message
from src.prompts import get_prompt
from src.strategies.base import BaseStrategy


class DirectStrategy(BaseStrategy):
    """Direct prompting strategy: ask the question as-is, no chain-of-thought."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self._config = config or {}

    def build_prompt(self, sample: Dict[str, Any]) -> List[Message]:
        """Build a straightforward prompt based on task_type."""
        task_type = sample.get("task_type", "text_qa")
        question = sample.get("question", "")

        if task_type in ("text_exam", "image_mcq"):
            options = sample.get("options", {})
            options_text = "\n".join(
                f"{k}. {v}" for k, v in sorted(options.items())
            )
            user_content = get_prompt("direct", "user_exam", question=question, options_text=options_text)
        elif task_type == "text_qa":
            user_content = get_prompt("direct", "user_qa", question=question)
        else:
            user_goal = sample.get("user_goal", question)
            user_content = get_prompt("direct", "user_default", user_goal=user_goal)

        return [Message(role="user", content=user_content.strip())]

    def parse_output(self, raw_output: str, sample: Dict[str, Any]) -> Dict[str, Any]:
        """Extract the answer from the model's raw output.

        For choice tasks, extract the first uppercase letter (A-D).
        For QA tasks, return the full output as the answer.
        """
        task_type = sample.get("task_type", "text_qa")

        if task_type in ("text_exam", "image_mcq"):
            match = re.search(r"\b([A-D])\b", raw_output)
            parsed_answer = match.group(1) if match else raw_output.strip()
        else:
            parsed_answer = raw_output.strip()

        return {
            "parsed_answer": parsed_answer,
            "reasoning_trace": None,
        }
