"""
Unit tests for toolsim.experiment_runner.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toolsim.experiment_runner import (
    ExperimentRunner,
    build_file_search_demo_calls,
    build_file_search_demo_goals,
)
from toolsim.world_state import WorldState


def test_experiment_runner_executes_tool_calls_in_order():
    runner = ExperimentRunner()
    result = runner.run(
        tool_calls=[
            {"tool_name": "file.write", "args": {"file_id": "f1", "content": "hello"}},
            {"tool_name": "file.read", "args": {"file_id": "f1"}},
        ]
    )

    assert len(result.trace) == 2
    assert result.trace[0].tool_name == "file.write"
    assert result.trace[1].tool_name == "file.read"
    assert result.final_state.get_entity("file", "f1")["content"] == "hello"


def test_experiment_runner_trace_length_matches_tool_calls():
    runner = ExperimentRunner()
    tool_calls = build_file_search_demo_calls()

    result = runner.run(tool_calls=tool_calls)

    assert len(result.trace) == len(tool_calls)


def test_experiment_runner_outputs_call_level_metrics():
    runner = ExperimentRunner()
    result = runner.run(
        tool_calls=[
            {"tool_name": "file.write", "args": {"file_id": "f1", "content": "hello"}},
            {"tool_name": "missing.tool", "args": {}},
        ]
    )

    assert result.call_metrics.total_calls == 2
    assert result.call_metrics.successful_calls == 1
    assert result.call_metrics.failed_calls == 1
    assert result.all_calls_succeeded is False


def test_experiment_runner_outputs_state_level_metrics_when_goals_present():
    runner = ExperimentRunner()
    result = runner.run(
        tool_calls=build_file_search_demo_calls(),
        goals=build_file_search_demo_goals(),
    )

    assert result.state_metrics is not None
    assert result.state_metrics.goal_count == 3
    assert result.state_metrics.passed_count == 3
    assert result.state_metrics.all_passed is True


def test_experiment_runner_keeps_full_trace_when_a_call_fails():
    runner = ExperimentRunner()
    tool_calls = [
        {"tool_name": "file.write", "args": {"file_id": "f1", "content": "hello"}},
        {"tool_name": "missing.tool", "args": {}},
        {"tool_name": "file.read", "args": {"file_id": "f1"}},
    ]

    result = runner.run(tool_calls=tool_calls)

    assert len(result.trace) == 3
    assert result.trace[1].success is False
    assert result.trace[2].success is True


def test_experiment_runner_demo_file_search_flow_behaves_as_expected():
    runner = ExperimentRunner()
    result = runner.run(
        tool_calls=build_file_search_demo_calls(),
        goals=build_file_search_demo_goals(),
        initial_state=WorldState(),
    )

    assert result.trace[1].tool_name == "search.query"
    assert result.trace[1].observation["hits"] == []
    assert result.trace[3].tool_name == "search.query"
    assert len(result.trace[3].observation["hits"]) == 1
    assert result.trace[3].observation["hits"][0]["file_id"] == "f1"
    assert result.final_state.get_entity("search_index", "f1") is not None
    assert result.state_metrics is not None
    assert result.state_metrics.all_passed is True


def run_all_tests() -> None:
    test_experiment_runner_executes_tool_calls_in_order()
    test_experiment_runner_trace_length_matches_tool_calls()
    test_experiment_runner_outputs_call_level_metrics()
    test_experiment_runner_outputs_state_level_metrics_when_goals_present()
    test_experiment_runner_keeps_full_trace_when_a_call_fails()
    test_experiment_runner_demo_file_search_flow_behaves_as_expected()
    print("All experiment_runner tests passed!")


if __name__ == "__main__":
    run_all_tests()
