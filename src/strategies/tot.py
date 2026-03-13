"""
Tree-of-Thought strategy — calls vendor/tree-of-thought-llm BFS search directly.

Reference: https://github.com/princeton-nlp/tree-of-thought-llm
The vendor repo implements the full BFS generate -> evaluate -> select loop
in ``tot.methods.bfs.solve()``. We create a ``BenchmarkTask`` adapter that
implements the ``Task`` interface required by ``solve()`` and monkey-patch
``tot.models.gpt`` to route all LLM calls through our LangChain ChatOpenAI.
"""

import os
import re
import sys
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

from loguru import logger

from src.api.schemas import Message
from src.langchain_bridge import TokenUsageTracker, make_langchain_llm
from src.strategies.base import BaseStrategy

# ---------------------------------------------------------------------------
# Make the vendor package importable
# ---------------------------------------------------------------------------
_VENDOR_TOT_SRC = os.path.join(
    os.path.dirname(__file__), os.pardir, os.pardir, "vendor", "tree-of-thought-llm", "src"
)
if os.path.isdir(_VENDOR_TOT_SRC) and _VENDOR_TOT_SRC not in sys.path:
    sys.path.insert(0, os.path.abspath(_VENDOR_TOT_SRC))


# ---------------------------------------------------------------------------
# BenchmarkTask — adapter from our sample dict to the ``Task`` interface
# expected by ``tot.methods.bfs.solve()``.
# ---------------------------------------------------------------------------

class BenchmarkTask:
    """Wraps a single benchmark sample as a princeton-nlp ``Task``.

    All prompt templates are read from ``configs/strategies/tot.yaml``
    and passed in via constructor kwargs. No prompts are hardcoded.

    Required interface used by ``bfs.solve()``:
      - ``get_input(idx)`` -> str
      - ``steps``          -> int
      - ``stops``          -> list[str|None]
      - ``standard_prompt_wrap(x, y)`` -> str
      - ``cot_prompt_wrap(x, y)``      -> str
      - ``value_prompt_wrap(x, y)``    -> str
      - ``value_outputs_unwrap(x, y, value_outputs)`` -> float
      - ``value_cache``    -> dict
    """

    # -- Default templates (used only if YAML config is empty) --
    _DEFAULT_GENERATE_COT = (
        "{problem}\n\nLet's think step by step.\n{thoughts}"
    )
    _DEFAULT_GENERATE_STANDARD = (
        "{problem}\n\nProvide the next step of reasoning. "
        "Think carefully and give one concise step.\n{thoughts}"
    )
    _DEFAULT_EVALUATE_VALUE = (
        "Evaluate this partial solution to the problem.\n"
        "Problem: {problem}\n"
        "Current solution path:\n{thoughts}\n\n"
        "Rate as: sure/likely/impossible"
    )
    _DEFAULT_EVALUATE_VOTE = (
        "Given the following problem and candidate solutions, "
        "decide which is most promising.\n\n"
        "Problem: {problem}\n\n{choices}\n\n"
        'Conclude with "The best choice is {{s}}" '
        "where s is the integer id.\n"
    )

    def __init__(
        self,
        problem: str,
        steps: int = 3,
        generate_cot_tpl: str = "",
        generate_standard_tpl: str = "",
        evaluate_value_tpl: str = "",
        evaluate_vote_tpl: str = "",
    ) -> None:
        self._problem = problem
        self.steps = steps
        self.stops = [None] * steps
        self.value_cache: Dict[str, float] = {}
        self._generate_cot_tpl = generate_cot_tpl or self._DEFAULT_GENERATE_COT
        self._generate_standard_tpl = generate_standard_tpl or self._DEFAULT_GENERATE_STANDARD
        self._evaluate_value_tpl = evaluate_value_tpl or self._DEFAULT_EVALUATE_VALUE
        self._evaluate_vote_tpl = evaluate_vote_tpl or self._DEFAULT_EVALUATE_VOTE

    def __len__(self) -> int:
        return 1

    def get_input(self, idx: int) -> str:
        return self._problem

    # -- generation prompt wrappers (used by get_samples) --
    def standard_prompt_wrap(self, x: str, y: str = "") -> str:
        return self._generate_standard_tpl.format(problem=x, thoughts=y)

    def cot_prompt_wrap(self, x: str, y: str = "") -> str:
        return self._generate_cot_tpl.format(problem=x, thoughts=y)

    # -- propose (not used in sample mode, but required by interface) --
    def propose_prompt_wrap(self, x: str, y: str = "") -> str:
        return self.standard_prompt_wrap(x, y)

    # -- evaluation prompt wrappers (used by get_value / get_votes) --
    def value_prompt_wrap(self, x: str, y: str) -> str:
        return self._evaluate_value_tpl.format(problem=x, thoughts=y)

    @staticmethod
    def value_outputs_unwrap(x: str, y: str, value_outputs: list) -> float:
        value_map = {"impossible": 0.001, "likely": 1, "sure": 20}
        total = 0.0
        for out in value_outputs:
            last = out.strip().split("\n")[-1].strip().lower()
            for key, val in value_map.items():
                if key in last:
                    total += val
                    break
            else:
                total += 1.0
        return total

    def vote_prompt_wrap(self, x: str, ys: list) -> str:
        choices = ""
        for i, y in enumerate(ys, 1):
            choices += f"Choice {i}:\n{y}\n"
        return self._evaluate_vote_tpl.format(problem=x, choices=choices)

    @staticmethod
    def vote_outputs_unwrap(vote_outputs: list, n_candidates: int) -> list:
        votes = [0] * n_candidates
        for out in vote_outputs:
            m = re.search(r"best choice is\D*(\d+)", out, re.I)
            if m:
                idx = int(m.group(1)) - 1
                if 0 <= idx < n_candidates:
                    votes[idx] += 1
        return votes


class ToTStrategy(BaseStrategy):
    """Tree-of-Thought strategy backed by vendor/tree-of-thought-llm BFS.

    Calls ``tot.methods.bfs.solve()`` from the vendor repo, monkey-patching
    ``tot.models.gpt`` so all LLM calls go through our LangChain ChatOpenAI.

    Reads config from configs/strategies/tot.yaml.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__("tot", config)
        tot_cfg = self._yaml_cfg.get("tot_config", {})
        self._k = self._runtime_cfg.get("k", tot_cfg.get("k", 3))
        self._depth = self._runtime_cfg.get("depth", tot_cfg.get("depth", 3))
        self._n_select = self._runtime_cfg.get(
            "n_select_sample", tot_cfg.get("n_select_sample", self._k)
        )
        self._n_evaluate = self._runtime_cfg.get(
            "n_evaluate_sample", tot_cfg.get("n_evaluate_sample", 3)
        )
        self._method_generate = self._runtime_cfg.get(
            "method_generate", tot_cfg.get("method_generate", "sample")
        )
        self._method_evaluate = self._runtime_cfg.get(
            "method_evaluate", tot_cfg.get("method_evaluate", "value")
        )
        self._method_select = self._runtime_cfg.get(
            "method_select", tot_cfg.get("method_select", "greedy")
        )
        self._prompt_sample = self._runtime_cfg.get(
            "prompt_sample", tot_cfg.get("prompt_sample", "cot")
        )

    @property
    def k(self) -> int:
        return self._k

    @property
    def depth(self) -> int:
        return self._depth

    # ------------------------------------------------------------------
    # Core: call vendor bfs.solve() with monkey-patched gpt
    # ------------------------------------------------------------------

    def run_tot_bfs(
        self,
        sample: Dict[str, Any],
        model_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Run BFS tree search via vendor/tree-of-thought-llm.

        Monkey-patches ``tot.models.gpt`` to route LLM calls through
        our LangChain ChatOpenAI, then calls ``bfs.solve()``.

        Args:
            sample: The input sample dict.
            model_config: Model config for make_langchain_llm.

        Returns:
            Dict with raw_output, parsed_answer, reasoning_trace, usage.
        """
        import tot.models as tot_models
        import tot.methods.bfs as bfs_module
        from tot.methods.bfs import solve as bfs_solve

        llm = make_langchain_llm(model_config)
        tracker = TokenUsageTracker()

        # Reset vendor token counters
        tot_models.completion_tokens = 0
        tot_models.prompt_tokens = 0

        # Monkey-patch gpt() to use our LLM
        _original_models_gpt = tot_models.gpt
        _original_bfs_gpt = bfs_module.gpt

        def _patched_gpt(prompt, model=None, temperature=0.7, max_tokens=1000, n=1, stop=None):
            from langchain_core.messages import HumanMessage
            from concurrent.futures import ThreadPoolExecutor, as_completed

            def _single_call():
                resp = llm.invoke(
                    [HumanMessage(content=prompt)],
                    config={"callbacks": [tracker]},
                    stop=stop,
                )
                return resp.content if hasattr(resp, "content") else str(resp)

            if n == 1:
                return [_single_call()]

            # Parallelize n>1 LLM calls for speed
            logger.debug(f"ToT _patched_gpt: parallel {n} calls, prompt_len={len(prompt)}")
            outputs = []
            with ThreadPoolExecutor(max_workers=n) as pool:
                futures = [pool.submit(_single_call) for _ in range(n)]
                for f in futures:
                    outputs.append(f.result())
            return outputs

        # Patch both the models module and the bfs module reference
        tot_models.gpt = _patched_gpt
        bfs_module.gpt = _patched_gpt

        try:
            # Build task adapter and args namespace, reading templates from YAML
            problem = self.build_problem_description(sample)
            task = BenchmarkTask(
                problem=problem,
                steps=self._depth,
                generate_cot_tpl=self._prompts.get("generate_cot", ""),
                generate_standard_tpl=self._prompts.get("generate_standard", ""),
                evaluate_value_tpl=self._prompts.get("evaluate_value", ""),
                evaluate_vote_tpl=self._prompts.get("evaluate_vote", ""),
            )

            args = SimpleNamespace(
                backend=model_config.get("model", "deepseek-chat"),
                temperature=model_config.get("temperature", 0.7),
                n_generate_sample=self._k,
                n_evaluate_sample=self._n_evaluate,
                n_select_sample=self._n_select,
                method_generate=self._method_generate,
                method_evaluate=self._method_evaluate,
                method_select=self._method_select,
                prompt_sample=self._prompt_sample,
            )

            logger.info(f"ToT: calling bfs_solve with depth={self._depth}, k={self._k}")
            ys, info = bfs_solve(args, task, 0, to_print=False)
            logger.info(f"ToT: bfs_solve returned {len(ys)} candidates")

            best = ys[0] if ys else ""

            # Final answer extraction (template from YAML config)
            extract_tpl = self._prompts.get("extract_answer", "").strip()
            if extract_tpl:
                final_prompt = extract_tpl.format(
                    problem=problem, best_candidate=best
                )
            else:
                final_prompt = (
                    f"{problem}\n\n"
                    f"Based on this reasoning:\n{best}\n\n"
                    f"Provide your final answer. End with: Answer: <your answer>"
                )
            from langchain_core.messages import HumanMessage
            final_resp = llm.invoke(
                [HumanMessage(content=final_prompt)],
                config={"callbacks": [tracker]},
            )
            final_text = (
                final_resp.content
                if hasattr(final_resp, "content")
                else str(final_resp)
            )

            parsed = self.parse_output(final_text, sample)

            # Build reasoning trace from bfs info (unified schema)
            steps_info = info.get("steps", [])
            reasoning_trace = []
            for s in steps_info:
                selected = s.get("select_new_ys", [])
                reasoning_trace.append({
                    "step": s["step"] + 1,
                    "type": "tree_search",
                    "content": "; ".join(y[:120] for y in selected) if selected else "(no candidates selected)",
                    "num_candidates": len(s.get("new_ys", [])),
                    "values": s.get("values", []),
                    "selected": [y[:80] for y in selected],
                })

            return {
                "raw_output": final_text,
                "parsed_answer": parsed["parsed_answer"],
                "reasoning_trace": reasoning_trace,
                "usage": tracker.to_usage_dict(),
            }
        finally:
            tot_models.gpt = _original_models_gpt
            bfs_module.gpt = _original_bfs_gpt

    # ------------------------------------------------------------------
    # Prompt building (fallback for non-BFS paths)
    # ------------------------------------------------------------------

    def build_prompt(self, sample: Dict[str, Any], **kwargs: Any) -> List[Message]:
        """Build the thought-generation prompt for a single branch."""
        task_type = sample.get("task_type", "text_qa")

        prompt_id = self.resolve_prompt(task_type)
        if prompt_id:
            self._resolved_prompt_id = prompt_id
            return self.build_messages_from_prompt_id(
                prompt_id, **self.build_template_vars(sample)
            )

        question = sample.get("question", "")
        system = self._prompts.get("system", "")
        messages: List[Message] = []
        if system and system.strip():
            messages.append(Message(role="system", content=system.strip()))

        if task_type in ("text_exam", "image_mcq"):
            options = sample.get("options", {})
            options_text = "\n".join(
                f"{k}. {v}" for k, v in sorted(options.items())
            )
            user_content = self.render_prompt(
                "user_exam", question=question, options_text=options_text
            )
        else:
            user_content = self.render_prompt("user_qa", question=question)

        messages.append(Message(role="user", content=user_content.strip()))
        return messages

    def build_problem_description(self, sample: Dict[str, Any]) -> str:
        """Build the problem description string for the BFS search."""
        task_type = sample.get("task_type", "text_qa")
        question = sample.get("question", "")
        if task_type in ("text_exam", "image_mcq"):
            options = sample.get("options", {})
            options_text = "\n".join(
                f"{k}. {v}" for k, v in sorted(options.items())
            )
            return f"{question}\n\n{options_text}"
        return question

    def build_checker_prompt(
        self, thoughts: str, sample: Dict[str, Any]
    ) -> List[Message]:
        """Build the checker/evaluation prompt for candidate thoughts."""
        question = sample.get("question", "")
        checker_text = self.render_prompt(
            "checker_template", question=question, thoughts=thoughts
        )
        return [Message(role="user", content=checker_text.strip())]

    def parse_tot_result(
        self, result: str, sample: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse a ToT result string into our standard format."""
        return self.parse_output(result, sample)
