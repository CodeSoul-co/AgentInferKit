import re
from collections import Counter
from typing import Any, Dict, List, Optional, Union

from src.api.schemas import Message
from src.strategies.base import BaseStrategy


class SelfConsistencyStrategy(BaseStrategy):
    """Self-Consistency strategy.

    Sample N diverse CoT reasoning paths (with temperature > 0), then
    take a majority vote over the extracted answers. The caller is
    responsible for generating multiple outputs; this class provides
    the prompt and the majority-vote aggregation logic.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self._config = config or {}
        self._num_samples = self._config.get("num_samples", 5)
        self._temperature = self._config.get("temperature", 0.7)

    def build_prompt(self, sample: Dict[str, Any]) -> List[Message]:
        """Build a CoT-style prompt (same for each sample path)."""
        task_type = sample.get("task_type", "text_qa")
        question = sample.get("question", "")

        if task_type in ("text_exam", "image_mcq"):
            options = sample.get("options", {})
            options_text = "\n".join(f"{k}. {v}" for k, v in sorted(options.items()))
            user_content = (
                f"{question}\n\n{options_text}\n\n"
                "Please think step by step, then provide your final answer "
                "on the last line in the format: Answer: X"
            )
        else:
            user_content = (
                f"{question}\n\n"
                "Please think step by step, then provide your final answer "
                "on the last line in the format: Answer: <your answer>"
            )

        return [Message(role="user", content=user_content)]

    def parse_output(
        self, raw_output: Union[str, List[str]], sample: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse one or multiple outputs and return majority-voted answer.

        Args:
            raw_output: Either a single string (one sample) or a list of
                        strings (multiple samples for majority voting).
            sample: The original sample dict.

        Returns:
            Dict with parsed_answer (majority vote), reasoning_trace,
            vote_distribution, and all_answers.
        """
        if isinstance(raw_output, str):
            raw_output = [raw_output]

        task_type = sample.get("task_type", "text_qa")
        all_answers: List[str] = []
        all_traces: List[str] = []

        for text in raw_output:
            answer, trace = self._extract_answer(text, task_type)
            all_answers.append(answer)
            all_traces.append(trace)

        # Majority vote
        counter = Counter(all_answers)
        majority_answer = counter.most_common(1)[0][0] if counter else ""

        return {
            "parsed_answer": majority_answer,
            "reasoning_trace": all_traces[0] if all_traces else None,
            "vote_distribution": dict(counter),
            "all_answers": all_answers,
        }

    def _extract_answer(self, text: str, task_type: str) -> tuple:
        """Extract answer and reasoning from a single output.

        Returns:
            Tuple of (answer_str, reasoning_str).
        """
        lines = text.strip().split("\n")
        answer_match = re.search(r"[Aa]nswer\s*:\s*(.+)", text)

        if answer_match:
            parsed = answer_match.group(1).strip()
            if task_type in ("text_exam", "image_mcq"):
                letter = re.search(r"\b([A-D])\b", parsed)
                if letter:
                    parsed = letter.group(1)
            reasoning = "\n".join(
                line for line in lines if not re.search(r"[Aa]nswer\s*:", line)
            ).strip()
            return parsed, reasoning

        if task_type in ("text_exam", "image_mcq"):
            letter = re.search(r"\b([A-D])\b", text)
            return (letter.group(1) if letter else text.strip()), text.strip()

        return (lines[-1].strip() if lines else text.strip()), text.strip()
