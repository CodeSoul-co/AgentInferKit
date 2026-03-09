"""
Agent Runner — drives LangChain AgentExecutor for api_calling tasks.

Uses ReActStrategy.create_executor() to build the agent, then runs each sample
through the AgentExecutor loop. Also supports ToTChain for ToT strategy.
"""

import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from loguru import logger

from src.adapters.base import BaseModelAdapter
from src.api.schemas import Message
from src.langchain_bridge import TokenUsageTracker
from src.runners.base import BaseRunner
from src.strategies.base import BaseStrategy
from src.toolsim.executor import MockExecutor
from src.toolsim.registry import ToolRegistry


class AgentRunner(BaseRunner):
    """Runner for agent/function-calling tasks using LangChain AgentExecutor.

    Supports:
      - ReAct strategy: uses AgentExecutor with Thought/Action/Observation loop
      - ToT strategy: uses langchain-experimental ToTChain
      - Other strategies: falls back to standard single-call via adapter
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
        self._tool_registry = ToolRegistry()
        self._mock_executor = MockExecutor(self._tool_registry)

    async def run_single(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """Run inference on a single api_calling sample."""
        start = time.perf_counter()
        strategy_name = self._strategy._strategy_name

        if strategy_name == "react":
            return await self._run_react(sample, start)
        elif strategy_name == "tot":
            return await self._run_tot(sample, start)
        else:
            return await self._run_standard(sample, start)

    async def _run_react(self, sample: Dict[str, Any], start: float) -> Dict[str, Any]:
        """Run the vendor ReAct Thought->Action->Observation loop."""
        from src.strategies.react import ReActStrategy

        strategy: ReActStrategy = self._strategy  # type: ignore
        tool_ids = sample.get("tool_index", sample.get("available_tools", []))
        tool_schemas = self._tool_registry.get_tools_for_sample(tool_ids)

        try:
            result = strategy.run_react_loop(sample, self._model_config, tool_schemas)
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            tracker = TokenUsageTracker()
            return self._build_prediction(
                sample, "", [], [], tracker, elapsed, error=str(e)
            )

        elapsed = (time.perf_counter() - start) * 1000
        tracker = TokenUsageTracker()
        usage = result.get("usage", {})
        tracker.prompt_tokens = usage.get("prompt_tokens", 0)
        tracker.completion_tokens = usage.get("completion_tokens", 0)
        tracker.total_latency_ms = usage.get("latency_ms", 0)

        return self._build_prediction(
            sample,
            result["raw_output"],
            result["reasoning_trace"],
            result.get("tool_trace", []),
            tracker,
            elapsed,
            parsed_answer=result["parsed_answer"],
        )

    async def _run_tot(self, sample: Dict[str, Any], start: float) -> Dict[str, Any]:
        """Run a ToT BFS search using princeton-nlp algorithm + LangChain."""
        from src.strategies.tot import ToTStrategy

        strategy: ToTStrategy = self._strategy  # type: ignore

        try:
            result = strategy.run_tot_bfs(sample, self._model_config)
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            tracker = TokenUsageTracker()
            return self._build_prediction(
                sample, "", [], [], tracker, elapsed, error=str(e)
            )

        elapsed = (time.perf_counter() - start) * 1000
        tracker = TokenUsageTracker()
        usage = result.get("usage", {})
        tracker.prompt_tokens = usage.get("prompt_tokens", 0)
        tracker.completion_tokens = usage.get("completion_tokens", 0)
        tracker.total_latency_ms = usage.get("latency_ms", 0)

        return self._build_prediction(
            sample,
            result["raw_output"],
            result.get("reasoning_trace", []),
            [],
            tracker,
            elapsed,
            parsed_answer=result["parsed_answer"],
        )

    async def _run_standard(self, sample: Dict[str, Any], start: float) -> Dict[str, Any]:
        """Fallback: run a standard single-call strategy via adapter."""
        messages = self._strategy.build_prompt(sample)
        result = await self._adapter.generate(messages)
        parsed = self._strategy.parse_output(result.content, sample)

        raw_trace = parsed.get("reasoning_trace")
        if isinstance(raw_trace, str) and raw_trace:
            reasoning_trace = [{"step": 1, "thought": raw_trace, "action": ""}]
        elif isinstance(raw_trace, list):
            reasoning_trace = raw_trace
        else:
            reasoning_trace = []

        elapsed = (time.perf_counter() - start) * 1000
        tracker = TokenUsageTracker()
        tracker.prompt_tokens = result.prompt_tokens
        tracker.completion_tokens = result.completion_tokens
        tracker.total_latency_ms = result.latency_ms

        return self._build_prediction(
            sample,
            result.content,
            reasoning_trace,
            [],
            tracker,
            elapsed,
            parsed_answer=parsed["parsed_answer"],
            error=result.error,
        )

    def _build_prediction(
        self,
        sample: Dict[str, Any],
        raw_output: str,
        reasoning_trace: Any,
        tool_trace: List[Dict[str, Any]],
        tracker: TokenUsageTracker,
        elapsed_ms: float,
        parsed_answer: str = "",
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Build a standardized prediction dict."""
        resolved_pid = getattr(self._strategy, "_resolved_prompt_id", None) or getattr(
            self._strategy, "_explicit_prompt_id", None
        )
        prompt_version = None
        if resolved_pid:
            try:
                from src.prompts.loader import get_prompt_version
                prompt_version = get_prompt_version(resolved_pid)
            except Exception:
                pass

        # Normalize reasoning_trace
        if isinstance(reasoning_trace, str) and reasoning_trace:
            reasoning_trace = [{"step": 1, "thought": reasoning_trace, "action": ""}]

        return {
            "sample_id": sample.get("sample_id", ""),
            "experiment_id": "",
            "model": "",
            "strategy": "",
            "prompt_id": resolved_pid or "",
            "prompt_version": prompt_version or "",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "input_prompt": "",
            "raw_output": raw_output,
            "parsed_answer": parsed_answer,
            "reasoning_trace": reasoning_trace if isinstance(reasoning_trace, list) else [],
            "rag_context": {"mode": None, "retrieved_chunks": []},
            "tool_trace": tool_trace,
            "usage": tracker.to_usage_dict() if tracker else {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "latency_ms": round(elapsed_ms, 1),
            },
            "error": error,
        }

    async def run_batch(
        self,
        samples: List[Dict[str, Any]],
        experiment_id: str,
        on_progress: Optional[Callable[[int, int, int], None]] = None,
    ) -> str:
        """Delegate to BatchRunner for batch execution."""
        raise NotImplementedError(
            "AgentRunner.run_batch() should be called via BatchRunner."
        )
