"""
Unit tests for toolsim.stateful_tracer.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toolsim.stateful_executor import ExecutionRecord, StatefulExecutor, create_default_tool_registry
from toolsim.stateful_tracer import TraceRecorder
from toolsim.world_state import WorldState


def test_trace_recorder_logs_multiple_records():
    recorder = TraceRecorder()
    record1 = ExecutionRecord(tool_name="file.write", success=True, pre_state_hash="a", post_state_hash="b")
    record2 = ExecutionRecord(tool_name="file.read", success=True, pre_state_hash="b", post_state_hash="b")

    recorder.log(record1)
    recorder.log(record2)

    records = recorder.get_records()
    assert len(records) == 2
    assert records[0].tool_name == "file.write"
    assert records[1].tool_name == "file.read"


def test_trace_recorder_clear_removes_all_records():
    recorder = TraceRecorder()
    recorder.log(ExecutionRecord(tool_name="file.write"))

    recorder.clear()

    assert recorder.get_records() == []


def test_trace_recorder_to_dict_list_exports_records():
    recorder = TraceRecorder()
    recorder.log(
        ExecutionRecord(
            tool_name="search.query",
            args={"query": "alpha"},
            success=True,
            observation={"hits": []},
            error=None,
            state_changed=False,
            pre_state_hash="x",
            post_state_hash="x",
            hash_changed=False,
        )
    )

    exported = recorder.to_dict_list()

    assert len(exported) == 1
    assert exported[0]["tool_name"] == "search.query"
    assert exported[0]["args"] == {"query": "alpha"}
    assert exported[0]["success"] is True
    assert exported[0]["pre_state_hash"] == "x"
    assert exported[0]["post_state_hash"] == "x"


def test_executor_with_tracer_auto_logs_records():
    ws = WorldState()
    tracer = TraceRecorder()
    executor = StatefulExecutor(create_default_tool_registry(), tracer=tracer)

    executor.execute("file.write", ws, {"file_id": "doc1", "content": "hello"})
    executor.execute("file.read", ws, {"file_id": "doc1"})

    records = tracer.get_records()
    assert len(records) == 2
    assert records[0].tool_name == "file.write"
    assert records[1].tool_name == "file.read"
    assert records[0].hash_changed is True
    assert records[1].hash_changed is False


def test_executor_without_tracer_still_executes_normally():
    ws = WorldState()
    executor = StatefulExecutor(create_default_tool_registry())

    record = executor.execute("file.write", ws, {"file_id": "doc1", "content": "hello"})

    assert record.success is True
    assert ws.get_entity("file", "doc1")["content"] == "hello"


def run_all_tests() -> None:
    test_trace_recorder_logs_multiple_records()
    test_trace_recorder_clear_removes_all_records()
    test_trace_recorder_to_dict_list_exports_records()
    test_executor_with_tracer_auto_logs_records()
    test_executor_without_tracer_still_executes_normally()
    print("All stateful_tracer tests passed!")


if __name__ == "__main__":
    run_all_tests()
