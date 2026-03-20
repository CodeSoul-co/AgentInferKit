"""
stateless_baseline.py — 最小可运行的 stateless baseline

语义约定：
  - 不使用显式 search_index
  - search.query 直接基于当前 file 内容做 substring matching
  - 仍复用 WorldState 作为最小共享存储
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from toolsim.evaluator import CallLevelEvaluator, StateEvaluationResult, StateGoalResult, StateLevelEvaluator
from toolsim.experiment_runner import ExperimentResult
from toolsim.file_tools import FILE_TOOLS
from toolsim.stateful_executor import StatefulExecutor
from toolsim.stateful_tracer import TraceRecorder
from toolsim.tool_spec import ToolExecutionResult, ToolSpec
from toolsim.world_state import WorldState


class StatelessSearchQueryTool(ToolSpec):
    """直接遍历当前 file 实体内容做 substring matching。"""

    tool_name: str = "search.query"
    description: str = (
        "Search current file contents directly using simple substring matching. "
        "No explicit search index is required."
    )
    input_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Substring to search for."},
        },
        "required": ["query"],
    }

    def execute(self, state: WorldState, args: Dict[str, Any]) -> ToolExecutionResult:
        query: Optional[str] = args.get("query")

        if not query:
            return ToolExecutionResult(
                success=False,
                error="Missing required argument: query",
                state_changed=False,
            )

        hits: List[Dict[str, Any]] = []
        for file_id, file_entity in state.entities.get("file", {}).items():
            content = file_entity.get("content", "")
            if query in content:
                hits.append(
                    {
                        "file_id": file_id,
                        "content": content,
                        "metadata": file_entity.get("metadata", {}),
                    }
                )

        return ToolExecutionResult(
            success=True,
            observation={
                "tool_name": self.tool_name,
                "query": query,
                "hits": hits,
            },
            state_changed=False,
        )


STATELESS_TOOLS: Dict[str, ToolSpec] = {
    **FILE_TOOLS,
    "search.query": StatelessSearchQueryTool(),
}


class StatelessStateLevelEvaluator(StateLevelEvaluator):
    """与 stateless query 语义对齐的最小 state-level evaluator。"""

    def _evaluate_goal(self, state: WorldState, goal: Dict[str, Any]) -> StateGoalResult:
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
    """与 stateful ExperimentRunner 接口相近的最小 stateless runner。"""

    def __init__(
        self,
        executor: Optional[StatefulExecutor] = None,
        call_evaluator: Optional[CallLevelEvaluator] = None,
        state_evaluator: Optional[StatelessStateLevelEvaluator] = None,
    ) -> None:
        self._executor = executor
        self._call_evaluator = call_evaluator or CallLevelEvaluator()
        self._state_evaluator = state_evaluator or StatelessStateLevelEvaluator()

    def run(
        self,
        tool_calls: List[Dict[str, Any]],
        initial_state: Optional[WorldState] = None,
        goals: Optional[List[Dict[str, Any]]] = None,
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
        state_metrics: Optional[StateEvaluationResult] = (
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
