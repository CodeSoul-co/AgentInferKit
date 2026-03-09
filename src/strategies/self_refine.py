"""
Self-Refine strategy — iterative generate, critique, refine loop.

Reference implementation: https://github.com/madaan/self-refine
LangChain integration: uses ChatOpenAI for each phase (generate, feedback, refine).
"""

from typing import Any, Dict, List, Optional

from loguru import logger

from src.api.schemas import Message
from src.langchain_bridge import TokenUsageTracker, make_langchain_llm
from src.strategies.base import BaseStrategy


class SelfRefineStrategy(BaseStrategy):
    """Self-Refine strategy with LangChain-backed multi-round refinement.

    Follows the three-phase iterative loop from madaan/self-refine:
      1. Generate an initial answer.
      2. Critique the answer (feedback).
      3. Refine the answer based on feedback.
    Repeats steps 2-3 for max_rounds or until the feedback says "looks good".

    Reads config from configs/strategies/self_refine.yaml.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__("self_refine", config)
        refine_cfg = self._yaml_cfg.get("refine_config", {})
        self._max_rounds = self._runtime_cfg.get("max_rounds", refine_cfg.get("max_rounds", 3))

    @property
    def max_rounds(self) -> int:
        return self._max_rounds

    # ------------------------------------------------------------------
    # LangChain-based refine loop
    # ------------------------------------------------------------------

    def run_refine_loop(
        self,
        sample: Dict[str, Any],
        model_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Run the full generate -> feedback -> refine loop using LangChain.

        Args:
            sample: The input sample dict.
            model_config: Model config dict for make_langchain_llm.

        Returns:
            Dict with keys: raw_output, parsed_answer, reasoning_trace, usage.
        """
        from langchain_core.messages import HumanMessage, SystemMessage

        llm = make_langchain_llm(model_config)
        tracker = TokenUsageTracker()

        reasoning_trace = []

        # Phase 1: Generate initial answer
        gen_messages = self.build_prompt(sample)
        lc_messages = []
        for m in gen_messages:
            if m.role == "system":
                lc_messages.append(SystemMessage(content=m.content))
            else:
                lc_messages.append(HumanMessage(content=m.content))

        response = llm.invoke(lc_messages, config={"callbacks": [tracker]})
        current_answer = response.content if hasattr(response, "content") else str(response)
        reasoning_trace.append({"step": 0, "phase": "generate", "output": current_answer})

        # Phases 2-3: Feedback + Refine loop
        for round_i in range(self._max_rounds):
            # Feedback phase
            fb_messages = self.build_feedback_prompt(sample, current_answer)
            lc_fb = [HumanMessage(content=fb_messages[0].content)]
            fb_response = llm.invoke(lc_fb, config={"callbacks": [tracker]})
            feedback_text = fb_response.content if hasattr(fb_response, "content") else str(fb_response)
            reasoning_trace.append({
                "step": round_i + 1,
                "phase": "feedback",
                "output": feedback_text,
            })

            # Check if feedback indicates no further improvement needed
            fb_lower = feedback_text.strip().lower()
            if any(phrase in fb_lower for phrase in ["looks good", "no error", "correct", "no issues", "no improvement"]):
                logger.debug(f"Self-Refine: stopping early at round {round_i + 1} — positive feedback")
                break

            # Refine phase
            ref_messages = self.build_refine_prompt(sample, current_answer, feedback_text)
            lc_ref = [HumanMessage(content=ref_messages[0].content)]
            ref_response = llm.invoke(lc_ref, config={"callbacks": [tracker]})
            current_answer = ref_response.content if hasattr(ref_response, "content") else str(ref_response)
            reasoning_trace.append({
                "step": round_i + 1,
                "phase": "refine",
                "output": current_answer,
            })

        parsed = self.parse_output(current_answer, sample)
        return {
            "raw_output": current_answer,
            "parsed_answer": parsed["parsed_answer"],
            "reasoning_trace": reasoning_trace,
            "usage": tracker.to_usage_dict(),
        }

    # ------------------------------------------------------------------
    # Prompt building
    # ------------------------------------------------------------------

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
        """Build the critique/feedback prompt (madaan/self-refine feedback phase)."""
        question = sample.get("question", "")
        content = self.render_prompt("feedback", question=question, previous_answer=previous_answer)
        return [Message(role="user", content=content.strip())]

    def build_refine_prompt(
        self, sample: Dict[str, Any], previous_answer: str, feedback: str
    ) -> List[Message]:
        """Build the refinement prompt (madaan/self-refine refine phase)."""
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
