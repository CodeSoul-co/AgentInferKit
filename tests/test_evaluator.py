"""
Unit tests for toolsim.evaluator.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toolsim.evaluator import CallLevelEvaluator, StateLevelEvaluator
from toolsim.stateful_executor import ExecutionRecord, StatefulExecutor, create_default_tool_registry
from toolsim.stateful_tracer import TraceRecorder
from toolsim.world_state import WorldState


def test_call_level_evaluator_counts_success_and_failure():
    evaluator = CallLevelEvaluator()
    records = [
        ExecutionRecord(tool_name="file.write", success=True),
        ExecutionRecord(tool_name="file.read", success=True),
        ExecutionRecord(tool_name="missing.tool", success=False),
    ]

    result = evaluator.evaluate(records)

    assert result.total_calls == 3
    assert result.successful_calls == 2
    assert result.failed_calls == 1
    assert result.success_rate == 2 / 3
    assert result.failed_rate == 1 / 3
    assert result.tool_counts["file.write"] == 1


def test_call_level_evaluator_accepts_trace_recorder():
    tracer = TraceRecorder()
    tracer.log(ExecutionRecord(tool_name="file.write", success=True))
    tracer.log(ExecutionRecord(tool_name="file.read", success=False))

    result = CallLevelEvaluator().evaluate(tracer)

    assert result.total_calls == 2
    assert result.successful_calls == 1
    assert result.failed_calls == 1


def test_state_level_evaluator_checks_entity_exists():
    ws = WorldState()
    executor = StatefulExecutor(create_default_tool_registry())
    executor.execute("file.write", ws, {"file_id": "f1", "content": "hello world"})

    result = StateLevelEvaluator().evaluate(
        ws,
        [{"type": "entity_exists", "entity_type": "file", "entity_id": "f1"}],
    )

    assert result.goal_count == 1
    assert result.passed_count == 1
    assert result.all_passed is True


def test_state_level_evaluator_checks_entity_field_equals():
    ws = WorldState()
    executor = StatefulExecutor(create_default_tool_registry())
    executor.execute("file.write", ws, {"file_id": "f1", "content": "hello world"})

    result = StateLevelEvaluator().evaluate(
        ws,
        [{
            "type": "entity_field_equals",
            "entity_type": "file",
            "entity_id": "f1",
            "field": "content",
            "expected": "hello world",
        }],
    )

    assert result.passed_count == 1
    assert result.failed_count == 0


def test_state_level_evaluator_checks_indexed_contains():
    ws = WorldState()
    executor = StatefulExecutor(create_default_tool_registry())
    executor.execute("file.write", ws, {"file_id": "f1", "content": "hello world"})
    executor.execute("search.index", ws, {"file_id": "f1"})

    result = StateLevelEvaluator().evaluate(
        ws,
        [{"type": "indexed_contains", "file_id": "f1", "substring": "hello"}],
    )

    assert result.passed_count == 1
    assert result.all_passed is True


def test_state_level_evaluator_checks_query_hits_file():
    ws = WorldState()
    executor = StatefulExecutor(create_default_tool_registry())
    executor.execute("file.write", ws, {"file_id": "f1", "content": "hello world"})
    executor.execute("search.index", ws, {"file_id": "f1"})

    result = StateLevelEvaluator().evaluate(
        ws,
        [{"type": "query_hits_file", "query": "hello", "file_id": "f1"}],
    )

    assert result.passed_count == 1
    assert result.failed_count == 0


def test_state_level_evaluator_mixed_goals_reports_counts():
    ws = WorldState()
    executor = StatefulExecutor(create_default_tool_registry())
    executor.execute("file.write", ws, {"file_id": "f1", "content": "hello world"})
    executor.execute("search.index", ws, {"file_id": "f1"})

    goals = [
        {"type": "entity_exists", "entity_type": "file", "entity_id": "f1"},
        {
            "type": "entity_field_equals",
            "entity_type": "file",
            "entity_id": "f1",
            "field": "content",
            "expected": "hello world",
        },
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
    test_call_level_evaluator_counts_success_and_failure()
    test_call_level_evaluator_accepts_trace_recorder()
    test_state_level_evaluator_checks_entity_exists()
    test_state_level_evaluator_checks_entity_field_equals()
    test_state_level_evaluator_checks_indexed_contains()
    test_state_level_evaluator_checks_query_hits_file()
    test_state_level_evaluator_mixed_goals_reports_counts()
    print("All evaluator tests passed!")


if __name__ == "__main__":
    run_all_tests()
