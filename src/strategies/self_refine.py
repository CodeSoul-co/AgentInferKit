import re
from typing import Any, Dict, List, Optional

from src.api.schemas import Message
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
            user_content = (
                f"{question}\n\n{options_text}\n\n"
                "Please think step by step and provide your answer "
                "on the last line as: Answer: X"
            )
        else:
            user_content = (
                f"{question}\n\n"
                "Please provide a thorough answer. "
                "Put your final answer on the last line as: Answer: <your answer>"
            )

        return [Message(role="user", content=user_content)]

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
        return [
            Message(
                role="user",
                content=(
                    f"Question: {question}\n\n"
                    f"Previous answer:\n{previous_answer}\n\n"
                    "Please critique this answer. Identify any errors, gaps, "
                    "or areas for improvement. Be specific and constructive."
                ),
            )
        ]

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

        suffix = "Answer: X" if task_type in ("text_exam", "image_mcq") else "Answer: <your answer>"

        return [
            Message(
                role="user",
                content=(
                    f"Question: {question}\n\n"
                    f"Previous answer:\n{previous_answer}\n\n"
                    f"Feedback:\n{feedback}\n\n"
                    f"Based on the feedback, provide an improved answer. "
                    f"Put your final answer on the last line as: {suffix}"
                ),
            )
        ]

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
