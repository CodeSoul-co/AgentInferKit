"""Stateless baseline runner.

Semantics:
  - No explicit search_index entities.
  - search.query directly searches current file content via substring matching.
  - Still reuses WorldState as minimal shared storage.
"""

from __future__ import annotations

from typing import Any

from toolsim.core.tool_spec import ToolExecutionResult, ToolSpec
from toolsim.core.world_state import WorldState
from toolsim.evaluators.evaluator import (
    CallLevelEvaluator,
    StateEvaluationResult,
    StateGoalResult,
    StateLevelEvaluator,
)
from toolsim.execution.stateful_executor import StatefulExecutor
from toolsim.execution.stateful_tracer import TraceRecorder
from toolsim.runners.experiment_runner import ExperimentResult
from toolsim.tools.file_tools import FILE_TOOLS


class StatelessSearchQueryTool(ToolSpec):
    """Search query that directly scans current file entity content via substring matching."""

    tool_name: str = "search.query"
    description: str = (
        "Search current file contents directly using simple substring matching. "
        "No explicit search index is required."
    )
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Substring to search for."},
        },
        "required": ["query"],
    }

    def execute(self, state: WorldState, args: dict[str, Any]) -> ToolExecutionResult:
        query: str | None = args.get("query")

        if not query:
            return ToolExecutionResult(
                success=False,
                error="Missing required argument: query",
                state_changed=False,
            )

        hits: list[dict[str, Any]] = []
        for file_id, file_entity in state.entities.get("file", {}).items():
            content = file_entity.get("content", "")
            if query in content:
                hits.append({
                    "file_id": file_id,
                    "content": content,
                    "metadata": file_entity.get("metadata", {}),
                })

        return ToolExecutionResult(
            success=True,
            observation={
                "tool_name": self.tool_name,
                "query": query,
                "hits": hits,
            },
            state_changed=False,
        )


STATELESS_TOOLS: dict[str, ToolSpec] = {
    **FILE_TOOLS,
    "search.query": StatelessSearchQueryTool(),
}


class StatelessStateLevelEvaluator(StateLevelEvaluator):
    """State-level evaluator aligned with stateless query semantics."""

    def _evaluate_goal(self, state: WorldState, goal: dict[str, Any]) -> StateGoalResult:
        goal_type = goal.get("type", "unknown")

        if goal_type == "indexed_contains":
            return StateGoalResult(
                goal_type=goal_type,
                passed=False,
                message="Goal unsupported in stateless baseline: indexed_contains",
            )

        if goal_type == "query_hits_file":
            query = goal.get("query", "")
            file_id = goal.get("file_id")
            query_result = StatelessSearchQueryTool().execute(state, {"query": query})
            hits = query_result.observation.get("hits", []) if query_result.success else []
            passed = any(hit.get("file_id") == file_id for hit in hits)
            return StateGoalResult(
                goal_type=goal_type,
                passed=passed,
                message=(
                    f"Query {query!r} hit file {file_id}"
                    if passed
                    else f"Query {query!r} did not hit file {file_id}"
                ),
            )

        return super()._evaluate_goal(state, goal)


class StatelessExperimentRunner:
    """Stateless experiment runner with an interface similar to :class:`ExperimentRunner`."""

    def __init__(
        self,
        executor: StatefulExecutor | None = None,
        call_evaluator: CallLevelEvaluator | None = None,
        state_evaluator: StatelessStateLevelEvaluator | None = None,
    ) -> None:
        self._executor = executor
        self._call_evaluator = call_evaluator or CallLevelEvaluator()
        self._state_evaluator = state_evaluator or StatelessStateLevelEvaluator()

    def run(
        self,
        tool_calls: list[dict[str, Any]],
        initial_state: WorldState | None = None,
        goals: list[dict[str, Any]] | None = None,
    ) -> ExperimentResult:
        state = initial_state if initial_state is not None else WorldState()
        tracer = TraceRecorder()
        executor = self._build_executor(tracer)

        for tool_call in tool_calls:
            tool_name = tool_call.get("tool_name", "")
            args = tool_call.get("args", {})
            executor.execute(tool_name, state, args)

        trace = tracer.get_records()
        call_metrics = self._call_evaluator.evaluate(trace)
        state_metrics: StateEvaluationResult | None = (
            self._state_evaluator.evaluate(state, goals) if goals is not None else None
        )

        return ExperimentResult(
            final_state=state,
            trace=trace,
            call_metrics=call_metrics,
            state_metrics=state_metrics,
            all_calls_succeeded=all(record.success for record in trace),
            final_state_hash=state.compute_hash(),
        )

    def _build_executor(self, tracer: TraceRecorder) -> StatefulExecutor:
        if self._executor is not None:
            return StatefulExecutor(self._executor._tools, tracer=tracer)
        return StatefulExecutor(STATELESS_TOOLS, tracer=tracer)
