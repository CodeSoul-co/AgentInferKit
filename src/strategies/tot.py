import re
from typing import Any, Dict, List, Optional

from src.api.schemas import Message
from src.prompts import get_prompt
from src.strategies.base import BaseStrategy


class ToTStrategy(BaseStrategy):
    """Tree-of-Thought strategy.

    Generates multiple candidate reasoning paths (thoughts), evaluates them,
    and selects the best one. This implementation provides prompt templates
    for the generation and evaluation phases; the actual tree search loop
    is orchestrated by the runner or caller.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self._config = config or {}
        self._num_candidates = self._config.get("num_candidates", 3)
        self._max_depth = self._config.get("max_depth", 2)

    def build_prompt(self, sample: Dict[str, Any]) -> List[Message]:
        """Build the thought-generation prompt for a single branch."""
        task_type = sample.get("task_type", "text_qa")
        question = sample.get("question", "")

        system_content = get_prompt("tot", "generation_system")
        messages = [Message(role="system", content=system_content.strip())]

        if task_type in ("text_exam", "image_mcq"):
            options = sample.get("options", {})
            options_text = "\n".join(f"{k}. {v}" for k, v in sorted(options.items()))
            user_content = get_prompt("tot", "user_exam", question=question, options_text=options_text)
        else:
            user_content = get_prompt("tot", "user_qa", question=question)

        messages.append(Message(role="user", content=user_content.strip()))
        return messages

    def build_eval_prompt(self, candidates: List[str], sample: Dict[str, Any]) -> List[Message]:
        """Build the evaluation/ranking prompt for candidate thoughts.

        Args:
            candidates: List of candidate reasoning strings.
            sample: The original sample.

        Returns:
            Messages for the evaluator LLM call.
        """
        question = sample.get("question", "")
        candidate_text = ""
        for i, c in enumerate(candidates, 1):
            candidate_text += f"\n--- Candidate {i} ---\n{c}\n"

        eval_system = get_prompt("tot", "eval_system")
        user_content = get_prompt("tot", "eval_user", question=question, candidate_text=candidate_text)
        return [
            Message(role="system", content=eval_system.strip()),
            Message(role="user", content=user_content.strip()),
        ]

    def parse_output(self, raw_output: str, sample: Dict[str, Any]) -> Dict[str, Any]:
        task_type = sample.get("task_type", "text_qa")

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
                parsed_answer = raw_output.strip().split("\n")[-1].strip()

        return {
            "parsed_answer": parsed_answer,
            "reasoning_trace": raw_output.strip(),
        }
