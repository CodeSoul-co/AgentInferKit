"""
Self-Consistency strategy — sample N CoT paths and majority vote.

Reference: CoT paper (Wang et al., 2022) — Self-Consistency Improves CoT Reasoning.
LangChain integration: uses ChatOpenAI with temperature>0 for diverse sampling.
"""

from collections import Counter
from typing import Any, Dict, List, Optional, Union

from loguru import logger

from src.api.schemas import Message
from src.langchain_bridge import TokenUsageTracker, make_langchain_llm
from src.strategies.base import BaseStrategy


class SelfConsistencyStrategy(BaseStrategy):
    """Self-Consistency strategy with LangChain-backed multi-sampling.

    Samples N diverse CoT reasoning paths (with temperature > 0) using
    LangChain ChatOpenAI, then takes a majority vote over extracted answers.

    Reads config from configs/strategies/self_consistency.yaml.
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

    # ------------------------------------------------------------------
    # LangChain-based consistency voting
    # ------------------------------------------------------------------

    def run_consistency_vote(
        self,
        sample: Dict[str, Any],
        model_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Sample N diverse CoT paths via LangChain and majority-vote.

        Args:
            sample: The input sample dict.
            model_config: Model config dict for make_langchain_llm.

        Returns:
            Dict with parsed_answer, reasoning_trace, vote_distribution, all_answers, usage.
        """
        from langchain_core.messages import HumanMessage, SystemMessage

        # Override temperature for diverse sampling
        sc_config = dict(model_config)
        sc_config["temperature"] = self._temperature
        llm = make_langchain_llm(sc_config)
        tracker = TokenUsageTracker()

        # Build the prompt once (same for all N paths)
        gen_messages = self.build_prompt(sample)
        lc_messages = []
        for m in gen_messages:
            if m.role == "system":
                lc_messages.append(SystemMessage(content=m.content))
            else:
                lc_messages.append(HumanMessage(content=m.content))

        # Sample N paths
        all_outputs: List[str] = []
        for i in range(self._num_samples):
            response = llm.invoke(lc_messages, config={"callbacks": [tracker]})
            text = response.content if hasattr(response, "content") else str(response)
            all_outputs.append(text)

        parsed = self.parse_output(all_outputs, sample)
        parsed["usage"] = tracker.to_usage_dict()
        return parsed

    # ------------------------------------------------------------------
    # Prompt building
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Output parsing
    # ------------------------------------------------------------------

    def parse_output(
        self, raw_output: Union[str, List[str]], sample: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse one or multiple outputs and return majority-voted answer."""
        if isinstance(raw_output, str):
            raw_output = [raw_output]

        task_type = sample.get("task_type", "text_qa")
        all_answers: List[str] = []
        all_traces: List[List] = []

        for text in raw_output:
            answer = self._extract_answer(text, task_type)
            trace = self._extract_trace(text)
            all_answers.append(answer)
            all_traces.append(trace)

        counter = Counter(all_answers)
        majority_answer = counter.most_common(1)[0][0] if counter else ""

        # Build a unified reasoning trace: each sampled path as a step
        reasoning_trace = []
        for i, (ans, trace_steps) in enumerate(zip(all_answers, all_traces)):
            reasoning_trace.append({
                "step": i + 1,
                "type": "sample_path",
                "content": f"Path {i+1} -> {ans}",
                "answer": ans,
                "sub_steps": trace_steps,
            })

        return {
            "parsed_answer": majority_answer,
            "reasoning_trace": reasoning_trace,
            "vote_distribution": dict(counter),
            "all_answers": all_answers,
        }
