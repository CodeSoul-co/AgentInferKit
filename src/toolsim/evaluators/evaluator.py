"""Call-level and state-level evaluators for toolsim execution traces."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Iterable, Sequence

if TYPE_CHECKING:
    from toolsim.execution.stateful_executor import ExecutionRecord
    from toolsim.execution.stateful_tracer import TraceRecorder

from toolsim.core.world_state import WorldState
from toolsim.tools.calendar_tools import CalendarSearchEventsTool
from toolsim.tools.search_tools import SearchQueryTool


@dataclass
class CallEvaluationResult:
    """Aggregate metrics from a sequence of execution records."""

    total_calls: int
    successful_calls: int
    failed_calls: int
    success_rate: float
    failed_rate: float
    partial_calls: int = 0
    pending_calls: int = 0
    invalid_calls: int = 0
    tool_counts: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "success_rate": self.success_rate,
            "failed_rate": self.failed_rate,
            "partial_calls": self.partial_calls,
            "pending_calls": self.pending_calls,
            "invalid_calls": self.invalid_calls,
            "tool_counts": self.tool_counts,
        }


@dataclass
class StateGoalResult:
    """Result of evaluating a single goal assertion."""

    goal_type: str
    passed: bool
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal_type": self.goal_type,
            "passed": self.passed,
            "message": self.message,
        }


@dataclass
class StateEvaluationResult:
    """Result of evaluating all goal assertions against a world state."""

    goal_count: int
    passed_count: int
    failed_count: int
    all_passed: bool
    details: list[StateGoalResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal_count": self.goal_count,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "all_passed": self.all_passed,
            "details": [detail.to_dict() for detail in self.details],
        }


class CallLevelEvaluator:
    """Aggregate per-call statistics from execution records."""

    def evaluate(
        self,
        records_or_tracer: Sequence["ExecutionRecord"] | "TraceRecorder",
    ) -> CallEvaluationResult:
        """Compute aggregate call-level metrics from a trace.

        Args:
            records_or_tracer: A list of records or a TraceRecorder instance.

        Returns:
            A CallEvaluationResult with aggregated metrics.
        """
        from toolsim.execution.stateful_tracer import TraceRecorder
        records = _normalize_records(records_or_tracer, TraceRecorder)
        total_calls = len(records)
        successful_calls = sum(1 for record in records if record.success)
        failed_calls = total_calls - successful_calls
        partial_calls = sum(1 for record in records if record.partial)
        pending_calls = sum(1 for record in records if record.async_pending)
        invalid_calls = sum(
            1 for record in records
            if any(not result.passed for result in [*record.permission_results, *record.precondition_results])
        )

        tool_counts: dict[str, int] = {}
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
            partial_calls=partial_calls,
            pending_calls=pending_calls,
            invalid_calls=invalid_calls,
            tool_counts=tool_counts,
        )


class StateLevelEvaluator:
    """Evaluate goal assertions against a final :class:`WorldState`."""

    def evaluate(
        self,
        state: WorldState,
        goals: Iterable[dict[str, Any]],
    ) -> StateEvaluationResult:
        """Check a list of goal assertions against the current world state.

        Args:
            state: The world state to evaluate.
            goals: Iterable of goal dicts with a ``type`` key.

        Returns:
            A StateEvaluationResult with per-goal results and summary.
        """
        details: list[StateGoalResult] = []
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

    def _evaluate_goal(self, state: WorldState, goal: dict[str, Any]) -> StateGoalResult:
        """Evaluate a single goal assertion."""
        goal_type = goal.get("type", "unknown")

        if goal_type == "entity_exists":
            entity_type = goal.get("entity_type")
            entity_id = goal.get("entity_id")
            entity = state.get_entity(entity_type, entity_id)
            passed = entity is not None
            msg = f"Entity exists: {entity_type}.{entity_id}" if passed else f"Entity missing: {entity_type}.{entity_id}"
            return StateGoalResult(goal_type=goal_type, passed=passed, message=msg)

        if goal_type == "entity_field_equals":
            entity_type = goal.get("entity_type")
            entity_id = goal.get("entity_id")
            field_name = goal.get("field")
            expected = goal.get("expected")
            entity = state.get_entity(entity_type, entity_id)
            if entity is None:
                return StateGoalResult(goal_type=goal_type, passed=False, message=f"Entity missing: {entity_type}.{entity_id}")
            actual = entity.get(field_name)
            passed = actual == expected
            msg = f"Field matched: {entity_type}.{entity_id}.{field_name} == {expected!r}" if passed else f"Field mismatch: {entity_type}.{entity_id}.{field_name} expected {expected!r}, got {actual!r}"
            return StateGoalResult(goal_type=goal_type, passed=passed, message=msg)

        if goal_type == "indexed_contains":
            file_id = goal.get("file_id")
            substring = goal.get("substring", "")
            index_entry = state.get_entity("search_index", file_id)
            if index_entry is None:
                return StateGoalResult(goal_type=goal_type, passed=False, message=f"Indexed file missing: {file_id}")
            indexed_content = index_entry.get("indexed_content_snapshot", "")
            passed = substring in indexed_content
            msg = f"Indexed content contains substring for file {file_id}" if passed else f"Indexed content does not contain substring for file {file_id}"
            return StateGoalResult(goal_type=goal_type, passed=passed, message=msg)

        if goal_type == "query_hits_file":
            query = goal.get("query", "")
            file_id = goal.get("file_id")
            query_result = SearchQueryTool().execute(state, {"query": query})
            hits = query_result.observation.get("hits", []) if query_result.success else []
            passed = any(hit.get("file_id") == file_id for hit in hits)
            msg = f"Query {query!r} hit file {file_id}" if passed else f"Query {query!r} did not hit file {file_id}"
            return StateGoalResult(goal_type=goal_type, passed=passed, message=msg)

        if goal_type == "event_exists":
            event_id = goal.get("event_id")
            event = state.get_entity("calendar_event", event_id)
            passed = event is not None
            msg = f"Event exists: {event_id}" if passed else f"Event missing: {event_id}"
            return StateGoalResult(goal_type=goal_type, passed=passed, message=msg)

        if goal_type == "event_field_equals":
            event_id = goal.get("event_id")
            field_name = goal.get("field")
            expected = goal.get("expected")
            event = state.get_entity("calendar_event", event_id)
            if event is None:
                return StateGoalResult(goal_type=goal_type, passed=False, message=f"Event missing: {event_id}")
            actual = event.get(field_name)
            passed = actual == expected
            msg = f"Event field matched: {event_id}.{field_name} == {expected!r}" if passed else f"Event field mismatch: {event_id}.{field_name} expected {expected!r}, got {actual!r}"
            return StateGoalResult(goal_type=goal_type, passed=passed, message=msg)

        if goal_type == "event_status_is":
            event_id = goal.get("event_id")
            expected_status = goal.get("status")
            event = state.get_entity("calendar_event", event_id)
            if event is None:
                return StateGoalResult(goal_type=goal_type, passed=False, message=f"Event missing: {event_id}")
            actual_status = event.get("status")
            passed = actual_status == expected_status
            msg = f"Event status matched: {event_id} == {expected_status!r}" if passed else f"Event status mismatch: {event_id} expected {expected_status!r}, got {actual_status!r}"
            return StateGoalResult(goal_type=goal_type, passed=passed, message=msg)

        if goal_type == "search_hits_event":
            event_id = goal.get("event_id")
            search_args = dict(goal.get("search_args", {}))
            query_result = CalendarSearchEventsTool().execute(state, search_args)
            hits = query_result.observation.get("hits", []) if query_result.success else []
            passed = any(hit.get("event_id") == event_id for hit in hits)
            msg = f"Calendar search hit event {event_id}" if passed else f"Calendar search did not hit event {event_id}"
            return StateGoalResult(goal_type=goal_type, passed=passed, message=msg)

        return StateGoalResult(goal_type=goal_type, passed=False, message=f"Unsupported goal type: {goal_type}")


def _normalize_records(
    records_or_tracer: Sequence["ExecutionRecord"] | "TraceRecorder",
    tracer_cls: type,
) -> list["ExecutionRecord"]:
    if isinstance(records_or_tracer, tracer_cls):
        return records_or_tracer.get_records()
    return list(records_or_tracer)
