"""
evaluator.py — 最小可运行的 evaluator 原型

提供：
  - CallLevelEvaluator
  - StateLevelEvaluator
  - 对应的结构化评估结果 dataclass
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Sequence

from toolsim.search_tools import SearchQueryTool
from toolsim.stateful_executor import ExecutionRecord
from toolsim.stateful_tracer import TraceRecorder
from toolsim.world_state import WorldState


@dataclass
class CallEvaluationResult:
    total_calls: int
    successful_calls: int
    failed_calls: int
    success_rate: float
    failed_rate: float
    tool_counts: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "success_rate": self.success_rate,
            "failed_rate": self.failed_rate,
            "tool_counts": self.tool_counts,
        }


@dataclass
class StateGoalResult:
    goal_type: str
    passed: bool
    message: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal_type": self.goal_type,
            "passed": self.passed,
            "message": self.message,
        }


@dataclass
class StateEvaluationResult:
    goal_count: int
    passed_count: int
    failed_count: int
    all_passed: bool
    details: List[StateGoalResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal_count": self.goal_count,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "all_passed": self.all_passed,
            "details": [detail.to_dict() for detail in self.details],
        }


class CallLevelEvaluator:
    """对执行记录做最小调用级统计。"""

    def evaluate(
        self,
        records_or_tracer: Sequence[ExecutionRecord] | TraceRecorder,
    ) -> CallEvaluationResult:
        records = _normalize_records(records_or_tracer)
        total_calls = len(records)
        successful_calls = sum(1 for record in records if record.success)
        failed_calls = total_calls - successful_calls

        tool_counts: Dict[str, int] = {}
        for record in records:
            tool_counts[record.tool_name] = tool_counts.get(record.tool_name, 0) + 1

        success_rate = (successful_calls / total_calls) if total_calls else 0.0
        failed_rate = (failed_calls / total_calls) if total_calls else 0.0

        return CallEvaluationResult(
            total_calls=total_calls,
            successful_calls=successful_calls,
            failed_calls=failed_calls,
            success_rate=success_rate,
            failed_rate=failed_rate,
            tool_counts=tool_counts,
        )


class StateLevelEvaluator:
    """对最终 WorldState 执行最小目标断言。"""

    def evaluate(self, state: WorldState, goals: Iterable[Dict[str, Any]]) -> StateEvaluationResult:
        details: List[StateGoalResult] = []

        for goal in goals:
            details.append(self._evaluate_goal(state, goal))

        goal_count = len(details)
        passed_count = sum(1 for detail in details if detail.passed)
        failed_count = goal_count - passed_count

        return StateEvaluationResult(
            goal_count=goal_count,
            passed_count=passed_count,
            failed_count=failed_count,
            all_passed=(failed_count == 0),
            details=details,
        )

    def _evaluate_goal(self, state: WorldState, goal: Dict[str, Any]) -> StateGoalResult:
        goal_type = goal.get("type", "unknown")

        if goal_type == "entity_exists":
            entity_type = goal.get("entity_type")
            entity_id = goal.get("entity_id")
            entity = state.get_entity(entity_type, entity_id)
            passed = entity is not None
            return StateGoalResult(
                goal_type=goal_type,
                passed=passed,
                message=(
                    f"Entity exists: {entity_type}.{entity_id}"
                    if passed
                    else f"Entity missing: {entity_type}.{entity_id}"
                ),
            )

        if goal_type == "entity_field_equals":
            entity_type = goal.get("entity_type")
            entity_id = goal.get("entity_id")
            field = goal.get("field")
            expected = goal.get("expected")
            entity = state.get_entity(entity_type, entity_id)

            if entity is None:
                return StateGoalResult(
                    goal_type=goal_type,
                    passed=False,
                    message=f"Entity missing: {entity_type}.{entity_id}",
                )

            actual = entity.get(field)
            passed = actual == expected
            return StateGoalResult(
                goal_type=goal_type,
                passed=passed,
                message=(
                    f"Field matched: {entity_type}.{entity_id}.{field} == {expected!r}"
                    if passed
                    else (
                        f"Field mismatch: {entity_type}.{entity_id}.{field} "
                        f"expected {expected!r}, got {actual!r}"
                    )
                ),
            )

        if goal_type == "indexed_contains":
            file_id = goal.get("file_id")
            substring = goal.get("substring", "")
            index_entry = state.get_entity("search_index", file_id)

            if index_entry is None:
                return StateGoalResult(
                    goal_type=goal_type,
                    passed=False,
                    message=f"Indexed file missing: {file_id}",
                )

            indexed_content = index_entry.get("indexed_content_snapshot", "")
            passed = substring in indexed_content
            return StateGoalResult(
                goal_type=goal_type,
                passed=passed,
                message=(
                    f"Indexed content contains substring for file {file_id}"
                    if passed
                    else f"Indexed content does not contain substring for file {file_id}"
                ),
            )

        if goal_type == "query_hits_file":
            query = goal.get("query", "")
            file_id = goal.get("file_id")
            query_result = SearchQueryTool().execute(state, {"query": query})
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

        return StateGoalResult(
            goal_type=goal_type,
            passed=False,
            message=f"Unsupported goal type: {goal_type}",
        )


def _normalize_records(
    records_or_tracer: Sequence[ExecutionRecord] | TraceRecorder,
) -> List[ExecutionRecord]:
    if isinstance(records_or_tracer, TraceRecorder):
        return records_or_tracer.get_records()
    return list(records_or_tracer)
