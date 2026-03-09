import re
from typing import Any, Dict, List, Optional

from src.api.schemas import Message
from src.prompts import get_prompt
from src.strategies.base import BaseStrategy


class SelfRefineStrategy(BaseStrategy):
    """Self-Refine strategy.

    Three-phase iterative loop:
      1. Generate an initial answer.
      2. Critique the answer (feedback).
      3. Refine the answer based on feedback.
    Phases 2-3 repeat for max_rounds. The caller drives the loop;
    this class provides prompt builders for each phase.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self._config = config or {}
        self._max_rounds = self._config.get("max_rounds", 3)

    def build_prompt(self, sample: Dict[str, Any], round_num: int = 1) -> List[Message]:
        """Build the initial-generation prompt (round 1)."""
        task_type = sample.get("task_type", "text_qa")
        question = sample.get("question", "")

        if task_type in ("text_exam", "image_mcq"):
            options = sample.get("options", {})
            options_text = "\n".join(f"{k}. {v}" for k, v in sorted(options.items()))
            user_content = get_prompt("self_refine", "user_exam", question=question, options_text=options_text)
        else:
            user_content = get_prompt("self_refine", "user_qa", question=question)

        return [Message(role="user", content=user_content.strip())]

    def build_feedback_prompt(
        self, sample: Dict[str, Any], previous_answer: str
    ) -> List[Message]:
        """Build the critique/feedback prompt.

        Args:
            sample: The original sample.
            previous_answer: The model's previous answer to critique.

        Returns:
            Messages asking the model to critique the answer.
        """
        question = sample.get("question", "")
        content = get_prompt("self_refine", "feedback", question=question, previous_answer=previous_answer)
        return [Message(role="user", content=content.strip())]

    def build_refine_prompt(
        self, sample: Dict[str, Any], previous_answer: str, feedback: str
    ) -> List[Message]:
        """Build the refinement prompt.

        Args:
            sample: The original sample.
            previous_answer: The previous answer.
            feedback: The critique feedback.

        Returns:
            Messages asking the model to improve the answer.
        """
        task_type = sample.get("task_type", "text_qa")
        question = sample.get("question", "")

        if task_type in ("text_exam", "image_mcq"):
            content = get_prompt("self_refine", "refine_exam", question=question, previous_answer=previous_answer, feedback=feedback)
        else:
            content = get_prompt("self_refine", "refine_qa", question=question, previous_answer=previous_answer, feedback=feedback)

        return [Message(role="user", content=content.strip())]

    def parse_output(self, raw_output: str, sample: Dict[str, Any]) -> Dict[str, Any]:
        task_type = sample.get("task_type", "text_qa")
        lines = raw_output.strip().split("\n")

        answer_match = re.search(r"[Aa]nswer\s*:\s*(.+)", raw_output)
        if answer_match:
            parsed_answer = answer_match.group(1).strip()
            if task_type in ("text_exam", "image_mcq"):
                letter = re.search(r"\b([A-D])\b", parsed_answer)
                if letter:
                    parsed_answer = letter.group(1)
        else:
            if task_type in ("text_exam", "image_mcq"):
                letter = re.search(r"\b([A-D])\b", raw_output)
                parsed_answer = letter.group(1) if letter else raw_output.strip()
            else:
                parsed_answer = lines[-1].strip() if lines else raw_output.strip()

        return {
            "parsed_answer": parsed_answer,
            "reasoning_trace": raw_output.strip(),
        }
