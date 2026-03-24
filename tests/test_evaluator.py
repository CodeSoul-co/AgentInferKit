"""
Unit tests for toolsim.evaluator.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toolsim.evaluators.evaluator import CallLevelEvaluator, StateLevelEvaluator
from toolsim.execution.stateful_executor import ExecutionRecord, StatefulExecutor, create_default_tool_registry
from toolsim.execution.stateful_tracer import TraceRecorder
from toolsim.core.tool_spec import ConditionCheckResult
from toolsim.core.world_state import WorldState


def _record(**kwargs):
    return ExecutionRecord(call_id=kwargs.pop("call_id", "call_test"), tool_name=kwargs.pop("tool_name", "tool.test"), **kwargs)


def test_call_level_evaluator_counts_success_failure_and_new_phase1_fields():
    evaluator = CallLevelEvaluator()
    records = [
        _record(tool_name="file.write", success=True, status="succeeded"),
        _record(tool_name="file.read", success=True, status="pending", partial=True, async_pending=True),
        _record(tool_name="missing.tool", success=False, status="failed", precondition_results=[ConditionCheckResult(kind="entity_exists", passed=False, message="missing")]),
    ]

    result = evaluator.evaluate(records)

    assert result.total_calls == 3
    assert result.successful_calls == 2
    assert result.failed_calls == 1
    assert result.success_rate == 2 / 3
    assert result.failed_rate == 1 / 3
    assert result.partial_calls == 1
    assert result.pending_calls == 1
    assert result.invalid_calls == 1
    assert result.tool_counts["file.write"] == 1


def test_call_level_evaluator_accepts_trace_recorder():
    tracer = TraceRecorder()
    tracer.log(_record(tool_name="file.write", success=True, status="succeeded"))
    tracer.log(_record(tool_name="file.read", success=False, status="failed"))

    result = CallLevelEvaluator().evaluate(tracer)

    assert result.total_calls == 2
    assert result.successful_calls == 1
    assert result.failed_calls == 1


def test_state_level_evaluator_checks_entity_exists():
    ws = WorldState()
    executor = StatefulExecutor(create_default_tool_registry())
    executor.execute("file.write", ws, {"file_id": "f1", "content": "hello world"})

    result = StateLevelEvaluator().evaluate(ws, [{"type": "entity_exists", "entity_type": "file", "entity_id": "f1"}])

    assert result.goal_count == 1
    assert result.passed_count == 1
    assert result.all_passed is True


def test_state_level_evaluator_checks_entity_field_equals():
    ws = WorldState()
    executor = StatefulExecutor(create_default_tool_registry())
    executor.execute("file.write", ws, {"file_id": "f1", "content": "hello world"})

    result = StateLevelEvaluator().evaluate(ws, [{"type": "entity_field_equals", "entity_type": "file", "entity_id": "f1", "field": "content", "expected": "hello world"}])

    assert result.passed_count == 1
    assert result.failed_count == 0


def test_state_level_evaluator_checks_indexed_contains():
    ws = WorldState()
    executor = StatefulExecutor(create_default_tool_registry())
    executor.execute("file.write", ws, {"file_id": "f1", "content": "hello world"})
    executor.execute("search.index", ws, {"file_id": "f1"})

    result = StateLevelEvaluator().evaluate(ws, [{"type": "indexed_contains", "file_id": "f1", "substring": "hello"}])

    assert result.passed_count == 1
    assert result.all_passed is True


def test_state_level_evaluator_checks_query_hits_file():
    ws = WorldState()
    executor = StatefulExecutor(create_default_tool_registry())
    executor.execute("file.write", ws, {"file_id": "f1", "content": "hello world"})
    executor.execute("search.index", ws, {"file_id": "f1"})

    result = StateLevelEvaluator().evaluate(ws, [{"type": "query_hits_file", "query": "hello", "file_id": "f1"}])

    assert result.passed_count == 1
    assert result.failed_count == 0


def test_state_level_evaluator_checks_calendar_goals():
    ws = WorldState(clock=5.0, policies={"calendar": {"allow_delete_started_event": True}})
    executor = StatefulExecutor(create_default_tool_registry())
    executor.execute(
        "calendar.create_event",
        ws,
        {"event_id": "evt1", "title": "Team Sync", "start_time": 10.0, "end_time": 11.0, "participants": ["alice", "bob"], "location": "Room A"},
        permissions={"calendar.create_event"},
    )
    executor.execute("calendar.delete_event", ws, {"event_id": "evt1"}, permissions={"calendar.delete_event"})

    goals = [
        {"type": "event_exists", "event_id": "evt1"},
        {"type": "event_field_equals", "event_id": "evt1", "field": "title", "expected": "Team Sync"},
        {"type": "event_status_is", "event_id": "evt1", "status": "cancelled"},
        {"type": "search_hits_event", "event_id": "evt1", "search_args": {"participant": "alice", "status": "cancelled"}},
    ]

    result = StateLevelEvaluator().evaluate(ws, goals)

    assert result.goal_count == 4
    assert result.passed_count == 4
    assert result.failed_count == 0
    assert result.all_passed is True


def test_state_level_evaluator_mixed_goals_reports_counts():
    ws = WorldState()
    executor = StatefulExecutor(create_default_tool_registry())
    executor.execute("file.write", ws, {"file_id": "f1", "content": "hello world"})
    executor.execute("search.index", ws, {"file_id": "f1"})

    goals = [
        {"type": "entity_exists", "entity_type": "file", "entity_id": "f1"},
        {"type": "entity_field_equals", "entity_type": "file", "entity_id": "f1", "field": "content", "expected": "hello world"},
        {"type": "indexed_contains", "file_id": "f1", "substring": "hello"},
        {"type": "query_hits_file", "query": "hello", "file_id": "f1"},
        {"type": "entity_exists", "entity_type": "file", "entity_id": "missing"},
    ]

    result = StateLevelEvaluator().evaluate(ws, goals)

    assert result.goal_count == 5
    assert result.passed_count == 4
    assert result.failed_count == 1
    assert result.all_passed is False
    assert len(result.details) == 5


def run_all_tests() -> None:
    test_call_level_evaluator_counts_success_failure_and_new_phase1_fields()
    test_call_level_evaluator_accepts_trace_recorder()
    test_state_level_evaluator_checks_entity_exists()
    test_state_level_evaluator_checks_entity_field_equals()
    test_state_level_evaluator_checks_indexed_contains()
    test_state_level_evaluator_checks_query_hits_file()
    test_state_level_evaluator_checks_calendar_goals()
    test_state_level_evaluator_mixed_goals_reports_counts()
    print("All evaluator tests passed!")


if __name__ == "__main__":
    run_all_tests()
