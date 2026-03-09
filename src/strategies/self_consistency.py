from collections import Counter
from typing import Any, Dict, List, Optional, Union

from src.api.schemas import Message
from src.strategies.base import BaseStrategy


class SelfConsistencyStrategy(BaseStrategy):
    """Self-Consistency strategy using LangChain LLMChain for multi-sampling.

    Reads config from configs/strategies/self_consistency.yaml.
    Samples N diverse CoT reasoning paths (with temperature > 0), then
    takes a majority vote over the extracted answers.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__("self_consistency", config)
        sc_cfg = self._yaml_cfg.get("sc_config", {})
        self._num_samples = self._runtime_cfg.get("num_samples", sc_cfg.get("num_samples", 5))
        self._temperature = self._runtime_cfg.get("temperature", sc_cfg.get("temperature", 0.7))

    @property
    def num_samples(self) -> int:
        return self._num_samples

    @property
    def temperature(self) -> float:
        return self._temperature

    def build_prompt(self, sample: Dict[str, Any], **kwargs: Any) -> List[Message]:
        """Build a CoT-style prompt (same for each sample path)."""
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

    def parse_output(
        self, raw_output: Union[str, List[str]], sample: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse one or multiple outputs and return majority-voted answer."""
        if isinstance(raw_output, str):
            raw_output = [raw_output]

        task_type = sample.get("task_type", "text_qa")
        all_answers: List[str] = []
        all_traces: List[str] = []

        for text in raw_output:
            answer = self._extract_answer(text, task_type)
            trace = self._extract_trace(text)
            all_answers.append(answer)
            all_traces.append(trace or "")

        counter = Counter(all_answers)
        majority_answer = counter.most_common(1)[0][0] if counter else ""

        return {
            "parsed_answer": majority_answer,
            "reasoning_trace": all_traces[0] if all_traces else None,
            "vote_distribution": dict(counter),
            "all_answers": all_answers,
        }
