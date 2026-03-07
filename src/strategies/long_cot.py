import re
from typing import Any, Dict, List, Optional

from src.api.schemas import Message
from src.strategies.base import BaseStrategy


class LongCoTStrategy(BaseStrategy):
    """Long Chain-of-Thought strategy.

    Similar to CoT but uses a stronger system prompt to encourage extended,
    multi-step reasoning with explicit intermediate conclusions before the
    final answer. Suitable for complex math, logic, and multi-hop QA.
    """

    SYSTEM_PROMPT = (
        "You are an expert problem solver. When given a question, think through "
        "it very carefully and thoroughly. Break the problem into sub-problems, "
        "solve each one step by step, verify your intermediate results, and only "
        "then state your final answer on the last line in the format:\n"
        "Answer: <your answer>"
    )

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self._config = config or {}

    def build_prompt(self, sample: Dict[str, Any]) -> List[Message]:
        task_type = sample.get("task_type", "text_qa")
        question = sample.get("question", "")

        messages: List[Message] = [
            Message(role="system", content=self.SYSTEM_PROMPT),
        ]

        if task_type in ("text_exam", "image_mcq"):
            options = sample.get("options", {})
            options_text = "\n".join(f"{k}. {v}" for k, v in sorted(options.items()))
            user_content = (
                f"{question}\n\n{options_text}\n\n"
                "Reason through each option carefully before selecting the correct one. "
                "Put your final answer on the last line as: Answer: X"
            )
        else:
            user_content = (
                f"{question}\n\n"
                "Think step by step, verifying each intermediate result. "
                "Put your final answer on the last line as: Answer: <your answer>"
            )

        messages.append(Message(role="user", content=user_content))
        return messages

    def parse_output(self, raw_output: str, sample: Dict[str, Any]) -> Dict[str, Any]:
        task_type = sample.get("task_type", "text_qa")
        lines = raw_output.strip().split("\n")

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
            if task_type in ("text_exam", "image_mcq"):
                letter_match = re.search(r"\b([A-D])\b", raw_output)
                parsed_answer = letter_match.group(1) if letter_match else raw_output.strip()
            else:
                parsed_answer = lines[-1].strip() if lines else raw_output.strip()
            reasoning_trace = raw_output.strip()
        else:
            if task_type in ("text_exam", "image_mcq"):
                letter_match = re.search(r"\b([A-D])\b", parsed_answer)
                if letter_match:
                    parsed_answer = letter_match.group(1)
            reasoning_trace = "\n".join(reasoning_lines).strip()

        return {
            "parsed_answer": parsed_answer,
            "reasoning_trace": reasoning_trace if reasoning_trace else None,
        }
