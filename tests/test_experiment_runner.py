"""
Unit tests for toolsim.experiment_runner.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toolsim.backends.mock_backend import MockBackend
from toolsim.backends.sandbox_backend import SandboxBackend
from toolsim.core.environment import ToolEnvironment
from toolsim.runners.experiment_runner import ExperimentRunner, build_file_search_demo_calls, build_file_search_demo_goals
from toolsim.core.world_state import WorldState


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
    result = runner.run(tool_calls=build_file_search_demo_calls(), goals=build_file_search_demo_goals())

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
    result = runner.run(tool_calls=build_file_search_demo_calls(), goals=build_file_search_demo_goals(), initial_state=WorldState())

    assert result.trace[1].tool_name == "search.query"
    assert result.trace[1].observation["hits"] == []
    assert result.trace[3].tool_name == "search.query"
    assert len(result.trace[3].observation["hits"]) == 1
    assert result.trace[3].observation["hits"][0]["file_id"] == "f1"
    assert result.final_state.get_entity("search_index", "f1") is not None
    assert result.state_metrics is not None
    assert result.state_metrics.all_passed is True


def test_experiment_runner_reuses_environment_for_delayed_effects():
    runner = ExperimentRunner()
    state = WorldState()
    environment = ToolEnvironment(state=state)

    result = runner.run(
        tool_calls=[
            {"tool_name": "file.write", "args": {"file_id": "f1", "content": "gamma wave", "schedule_search_reindex": True, "reindex_delay": 2.0}},
            {"tool_name": "search.query", "args": {"query": "gamma"}},
            {"tool_name": "search.query", "args": {"query": "gamma"}, "advance_time": 2.0},
        ],
        environment=environment,
    )

    assert len(result.trace) == 3
    assert result.trace[0].scheduled_effect_ids == ["eff_reindex_f1_1"]
    assert result.trace[1].observation["hits"] == []
    assert len(result.trace[2].observation["hits"]) == 1
    assert result.trace[2].observation["hits"][0]["file_id"] == "f1"
    assert state.get_pending_effect("eff_reindex_f1_1").status == "applied"


def test_experiment_runner_can_advance_time_without_external_environment_object():
    runner = ExperimentRunner()
    result = runner.run(
        tool_calls=[
            {"tool_name": "file.write", "args": {"file_id": "f1", "content": "delta note", "schedule_search_reindex": True, "reindex_delay": 1.0}},
            {"tool_name": "search.query", "args": {"query": "delta"}},
            {"tool_name": "search.query", "args": {"query": "delta"}, "advance_time": 1.0},
        ]
    )

    assert result.trace[1].observation["hits"] == []
    assert len(result.trace[2].observation["hits"]) == 1
    assert result.trace[2].applied_effect_count == 0
    assert result.final_state.get_entity("search_index", "f1") is not None


def test_experiment_runner_can_create_state_from_mock_backend():
    runner = ExperimentRunner(backend=MockBackend())
    result = runner.run(
        tool_calls=[
            {"tool_name": "file.write", "args": {"file_id": "f1", "content": "backend hello"}},
        ]
    )

    assert result.trace[0].backend_name == "mock"
    assert result.final_state.get_entity("file", "f1")["content"] == "backend hello"


def test_experiment_runner_can_run_calendar_flow_with_sandbox_backend():
    backend = SandboxBackend(session_id="runner_box")
    runner = ExperimentRunner(backend=backend)
    result = runner.run(
        tool_calls=[
            {"tool_name": "calendar.create_event", "args": {"event_id": "evt1", "title": "Planning", "start_time": 9.0, "end_time": 10.0, "participants": ["alice"]}},
            {"tool_name": "calendar.search_events", "args": {"participant": "alice"}},
        ],
        permissions={"calendar.create_event", "calendar.search_events"},
        backend=backend,
    )

    assert result.trace[0].backend_name == "sandbox"
    assert result.trace[1].observation["hits"][0]["event_id"] == "evt1"
    assert result.final_state.resources["sandbox_session"] == "runner_box"


def run_all_tests() -> None:
    test_experiment_runner_executes_tool_calls_in_order()
    test_experiment_runner_trace_length_matches_tool_calls()
    test_experiment_runner_outputs_call_level_metrics()
    test_experiment_runner_outputs_state_level_metrics_when_goals_present()
    test_experiment_runner_keeps_full_trace_when_a_call_fails()
    test_experiment_runner_demo_file_search_flow_behaves_as_expected()
    test_experiment_runner_reuses_environment_for_delayed_effects()
    test_experiment_runner_can_advance_time_without_external_environment_object()
    test_experiment_runner_can_create_state_from_mock_backend()
    test_experiment_runner_can_run_calendar_flow_with_sandbox_backend()
    print("All experiment_runner tests passed!")


if __name__ == "__main__":
    run_all_tests()
