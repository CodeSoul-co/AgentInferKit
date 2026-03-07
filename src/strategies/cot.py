import re
from typing import Any, Dict, List, Optional

from src.api.schemas import Message
from src.strategies.base import BaseStrategy


class CoTStrategy(BaseStrategy):
    """Chain-of-Thought prompting strategy.

    Instructs the model to think step by step before giving the final answer.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self._config = config or {}

    def build_prompt(self, sample: Dict[str, Any]) -> List[Message]:
        """Build a CoT prompt that asks the model to reason step by step."""
        task_type = sample.get("task_type", "text_qa")
        question = sample.get("question", "")

        if task_type in ("text_exam", "image_mcq"):
            options = sample.get("options", {})
            options_text = "\n".join(
                f"{k}. {v}" for k, v in sorted(options.items())
            )
            user_content = (
                f"{question}\n\n"
                f"{options_text}\n\n"
                "Please think step by step, then provide your final answer "
                "on the last line in the format: Answer: X"
            )
        elif task_type == "text_qa":
            user_content = (
                f"{question}\n\n"
                "Please think step by step, then provide your final answer "
                "on the last line in the format: Answer: <your answer>"
            )
        else:
            user_goal = sample.get("user_goal", question)
            user_content = (
                f"{user_goal}\n\n"
                "Please think step by step, then provide your final answer "
                "on the last line in the format: Answer: <your answer>"
            )

        return [Message(role="user", content=user_content)]

    def parse_output(self, raw_output: str, sample: Dict[str, Any]) -> Dict[str, Any]:
        """Extract the final answer and reasoning trace from CoT output.

        Looks for 'Answer: X' pattern at the end; everything before it
        is treated as the reasoning trace.
        """
        task_type = sample.get("task_type", "text_qa")
        lines = raw_output.strip().split("\n")

        # Try to find "Answer: ..." line
        answer_pattern = re.compile(r"[Aa]nswer\s*:\s*(.+)")
        parsed_answer = ""
        reasoning_lines = []
        found = False

        for line in lines:
            match = answer_pattern.search(line)
            if match:
                parsed_answer = match.group(1).strip()
                found = True
            else:
                reasoning_lines.append(line)

        if not found:
            # Fallback: for choice tasks, try extracting a single letter
            if task_type in ("text_exam", "image_mcq"):
                letter_match = re.search(r"\b([A-D])\b", raw_output)
                parsed_answer = letter_match.group(1) if letter_match else raw_output.strip()
            else:
                parsed_answer = lines[-1].strip() if lines else raw_output.strip()
            reasoning_trace = raw_output.strip()
        else:
            # For choice tasks, extract just the letter from the answer
            if task_type in ("text_exam", "image_mcq"):
                letter_match = re.search(r"\b([A-D])\b", parsed_answer)
                if letter_match:
                    parsed_answer = letter_match.group(1)
            reasoning_trace = "\n".join(reasoning_lines).strip()

        return {
            "parsed_answer": parsed_answer,
            "reasoning_trace": reasoning_trace if reasoning_trace else None,
        }
