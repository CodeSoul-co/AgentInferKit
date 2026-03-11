import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from src.adapters.base import BaseModelAdapter
from src.api.schemas import Message
from src.runners.base import BaseRunner
from src.strategies.base import BaseStrategy
from src.rag.context import inject_rag_context


class QARunner(BaseRunner):
    """Runner for text_qa tasks.

    Handles: build prompt -> (optional RAG) -> call model -> parse output -> prediction dict.
    Dispatches to multi-turn loops for tot, self_consistency, self_refine.
    """

    def __init__(
        self,
        adapter: BaseModelAdapter,
        strategy: BaseStrategy,
        model_config: Optional[Dict[str, Any]] = None,
        rag_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._adapter = adapter
        self._strategy = strategy
        self._model_config = model_config or {}
        self._rag_config = rag_config or {}

    async def run_single(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """Run inference on a single QA sample."""
        start = time.perf_counter()
        strategy_name = self._strategy._strategy_name

        # Multi-turn strategies: dispatch to their dedicated loops
        if strategy_name == "tot" and self._model_config:
            return await self._run_tot(sample)
        if strategy_name == "self_consistency" and self._model_config:
            return await self._run_self_consistency(sample)
        if strategy_name == "self_refine" and self._model_config:
            return await self._run_self_refine(sample)

        # Build prompt via strategy
        messages = self._strategy.build_prompt(sample)

        # Optional RAG context injection (supports retrieved + oracle modes)
        messages, rag_context = inject_rag_context(messages, sample, self._rag_config)

        # Call model
        result = await self._adapter.generate(messages)

        # Parse output
        parsed = self._strategy.parse_output(result.content, sample)

        # Normalize reasoning_trace to structured list format
        raw_trace = parsed.get("reasoning_trace")
        if isinstance(raw_trace, str) and raw_trace:
            reasoning_trace = [{"step": 1, "thought": raw_trace, "action": ""}]
        elif isinstance(raw_trace, list):
            reasoning_trace = raw_trace
        else:
            reasoning_trace = []

        # Resolve prompt_id and prompt_version from strategy
        resolved_pid = getattr(self._strategy, "_resolved_prompt_id", None) or getattr(self._strategy, "_explicit_prompt_id", None)
        prompt_version = None
        if resolved_pid:
            try:
                from src.prompts.loader import get_prompt_version
                prompt_version = get_prompt_version(resolved_pid)
            except Exception:
                pass

        # Build prediction dict (SCHEMA.md section 5)
        prediction = {
            "sample_id": sample.get("sample_id", ""),
            "experiment_id": "",
            "model": "",
            "strategy": "",
            "prompt_id": resolved_pid or "",
            "prompt_version": prompt_version or "",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "input_prompt": "\n".join(f"[{m.role}] {m.content}" for m in messages),
            "raw_output": result.content,
            "parsed_answer": parsed["parsed_answer"],
            "reasoning_trace": reasoning_trace,
            "rag_context": rag_context,
            "tool_trace": [],
            "usage": {
                "prompt_tokens": result.prompt_tokens,
                "completion_tokens": result.completion_tokens,
                "total_tokens": result.prompt_tokens + result.completion_tokens,
                "latency_ms": result.latency_ms,
            },
            "error": result.error,
        }
        return prediction

    async def _run_tot(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch to ToTStrategy.run_tot_bfs() for BFS tree search."""
        from src.strategies.tot import ToTStrategy
        strategy: ToTStrategy = self._strategy  # type: ignore
        result = strategy.run_tot_bfs(sample, self._model_config)
        return self._wrap_multi_turn_result(sample, result)

    async def _run_self_consistency(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch to SelfConsistencyStrategy.run_consistency_vote()."""
        from src.strategies.self_consistency import SelfConsistencyStrategy
        strategy: SelfConsistencyStrategy = self._strategy  # type: ignore
        result = strategy.run_consistency_vote(sample, self._model_config)
        return self._wrap_multi_turn_result(sample, result)

    async def _run_self_refine(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch to SelfRefineStrategy.run_refine_loop()."""
        from src.strategies.self_refine import SelfRefineStrategy
        strategy: SelfRefineStrategy = self._strategy  # type: ignore
        result = strategy.run_refine_loop(sample, self._model_config)
        return self._wrap_multi_turn_result(sample, result)

    def _wrap_multi_turn_result(
        self, sample: Dict[str, Any], result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Wrap a multi-turn strategy result into a standard prediction dict."""
        raw_trace = result.get("reasoning_trace")
        if isinstance(raw_trace, str) and raw_trace:
            reasoning_trace = [{"step": 1, "thought": raw_trace, "action": ""}]
        elif isinstance(raw_trace, list):
            reasoning_trace = raw_trace
        else:
            reasoning_trace = []

        resolved_pid = getattr(self._strategy, "_resolved_prompt_id", None) or getattr(self._strategy, "_explicit_prompt_id", None)
        prompt_version = None
        if resolved_pid:
            try:
                from src.prompts.loader import get_prompt_version
                prompt_version = get_prompt_version(resolved_pid)
            except Exception:
                pass

        usage = result.get("usage", {})
        return {
            "sample_id": sample.get("sample_id", ""),
            "experiment_id": "",
            "model": "",
            "strategy": "",
            "prompt_id": resolved_pid or "",
            "prompt_version": prompt_version or "",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "input_prompt": "",
            "raw_output": result.get("raw_output", ""),
            "parsed_answer": result.get("parsed_answer", ""),
            "reasoning_trace": reasoning_trace,
            "rag_context": result.get("rag_context", {"mode": None, "query_text": None, "retrieved_chunks": [], "retrieval_latency_ms": 0}),
            "tool_trace": result.get("tool_trace", []),
            "usage": {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
                "latency_ms": usage.get("latency_ms", 0),
            },
            "error": result.get("error"),
        }

    async def run_batch(
        self,
        samples: List[Dict[str, Any]],
        experiment_id: str,
        on_progress: Optional[Callable[[int, int, int], None]] = None,
    ) -> str:
        """Delegate to BatchRunner for batch execution."""
        raise NotImplementedError(
            "QARunner.run_batch() should be called via BatchRunner."
        )
