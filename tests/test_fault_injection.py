"""Unit tests for toolsim fault injection."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toolsim.execution.stateful_executor import ExecutorConfig
from toolsim.faults import FaultProfile
from toolsim.runners.experiment_runner import ExperimentRunner


def test_transient_failure_fails_once_then_recovers():
    runner = ExperimentRunner(
        executor_config=ExecutorConfig(
            fault_profile=FaultProfile(transient_failures={"file.write": 1})
        )
    )

    result = runner.run(
        tool_calls=[
            {"tool_name": "file.write", "args": {"file_id": "f1", "content": "hello"}},
            {"tool_name": "file.write", "args": {"file_id": "f1", "content": "hello"}},
        ]
    )

    assert result.trace[0].success is False
    assert "Transient failure injected" in (result.trace[0].error or "")
    assert result.trace[1].success is True
    assert result.final_state.get_entity("file", "f1")["content"] == "hello"


def test_latency_fault_is_reflected_in_duration():
    runner = ExperimentRunner(
        executor_config=ExecutorConfig(
            fault_profile=FaultProfile(latency_ms_by_tool={"file.write": 5})
        )
    )

    result = runner.run(
        tool_calls=[
            {"tool_name": "file.write", "args": {"file_id": "f1", "content": "hello"}},
        ]
    )

    assert result.trace[0].duration_ms >= 5


def test_stale_observation_replays_previous_observation():
    runner = ExperimentRunner(
        executor_config=ExecutorConfig(
            fault_profile=FaultProfile(stale_observation_tools={"search.query"})
        )
    )

    result = runner.run(
        tool_calls=[
            {"tool_name": "file.write", "args": {"file_id": "f1", "content": "old hello"}},
            {"tool_name": "search.index", "args": {"file_id": "f1"}},
            {"tool_name": "search.query", "args": {"query": "hello"}},
            {"tool_name": "file.write", "args": {"file_id": "f1", "content": "new gamma"}},
            {"tool_name": "search.index", "args": {"file_id": "f1"}},
            {"tool_name": "search.query", "args": {"query": "gamma"}},
        ]
    )

    first_hits = result.trace[2].observation["hits"]
    replayed_hits = result.trace[5].observation["hits"]
    assert first_hits[0]["content"] == "old hello"
    assert replayed_hits[0]["content"] == "old hello"


def test_vague_error_masks_underlying_error():
    runner = ExperimentRunner(
        executor_config=ExecutorConfig(
            fault_profile=FaultProfile(vague_error_tools={"file.read"})
        )
    )

    result = runner.run(
        tool_calls=[
            {"tool_name": "file.read", "args": {"file_id": "missing"}},
        ]
    )

    assert result.trace[0].success is False
    assert result.trace[0].error == "File must exist before read"

    permissive_runner = ExperimentRunner(
        executor_config=ExecutorConfig(
            strict_preconditions=False,
            fault_profile=FaultProfile(vague_error_tools={"file.read"}),
        )
    )
    permissive_result = permissive_runner.run(
        tool_calls=[
            {"tool_name": "file.read", "args": {"file_id": "missing"}},
        ]
    )

    assert permissive_result.trace[0].success is False
    assert permissive_result.trace[0].error == "Tool failed due to a temporary environment issue."


def test_timeout_and_schema_drift_fail_before_execution():
    runner = ExperimentRunner(
        executor_config=ExecutorConfig(
            fault_profile=FaultProfile(
                timeout_failures={"file.write": 1},
                schema_drift_failures={"search.query": 1},
            )
        )
    )

    result = runner.run(
        tool_calls=[
            {"tool_name": "file.write", "args": {"file_id": "f1", "content": "hello"}},
            {"tool_name": "file.write", "args": {"file_id": "f1", "content": "hello"}},
            {"tool_name": "search.query", "args": {"query": "hello"}},
        ]
    )

    assert result.trace[0].success is False
    assert result.trace[0].metadata["fault"] == "timeout"
    assert result.trace[1].success is True
    assert result.trace[2].success is False
    assert result.trace[2].metadata["fault"] == "schema_drift"


def test_vague_observation_masks_successful_observation():
    runner = ExperimentRunner(
        executor_config=ExecutorConfig(
            fault_profile=FaultProfile(vague_observation_tools={"file.write"})
        )
    )

    result = runner.run(
        tool_calls=[
            {"tool_name": "file.write", "args": {"file_id": "f1", "content": "hello"}},
        ]
    )

    assert result.trace[0].success is True
    assert result.trace[0].metadata["fault"] == "vague_observation"
    assert result.trace[0].observation == {
        "message": "Observation is unavailable or too vague to determine the exact result."
    }


def test_misleading_observation_replaces_successful_observation_once():
    runner = ExperimentRunner(
        executor_config=ExecutorConfig(
            fault_profile=FaultProfile(
                misleading_observations_by_tool={"search.query": {"hits": [{"file_id": "wrong"}], "count": 1}},
                misleading_observation_failures={"search.query": 1},
            )
        )
    )

    result = runner.run(
        tool_calls=[
            {"tool_name": "file.write", "args": {"file_id": "f1", "content": "hello"}},
            {"tool_name": "search.index", "args": {"file_id": "f1"}},
            {"tool_name": "search.query", "args": {"query": "hello"}},
            {"tool_name": "search.query", "args": {"query": "hello"}},
        ]
    )

    assert result.trace[2].metadata["fault"] == "misleading_observation"
    assert result.trace[2].observation["hits"][0]["file_id"] == "wrong"
    assert result.trace[3].observation["hits"][0]["file_id"] == "f1"
