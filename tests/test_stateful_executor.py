"""
Unit tests for toolsim.stateful_executor.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toolsim.tool_spec import ToolExecutionResult, ToolSpec
from toolsim.stateful_executor import (
    StatefulExecutor,
    create_default_tool_registry,
)
from toolsim.world_state import WorldState


class ExplodingTool(ToolSpec):
    tool_name = "test.explode"
    description = "Raise an exception to test executor error handling."
    input_schema = {"type": "object", "properties": {}}

    def execute(self, state: WorldState, args: dict) -> ToolExecutionResult:
        raise RuntimeError("boom")


def test_executor_calls_file_write_successfully():
    ws = WorldState()
    executor = StatefulExecutor(create_default_tool_registry())

    record = executor.execute("file.write", ws, {"file_id": "doc1", "content": "hello"})

    assert record.success is True
    assert record.state_changed is True
    assert record.hash_changed is True
    assert record.pre_state_hash != record.post_state_hash
    assert ws.get_entity("file", "doc1")["content"] == "hello"


def test_executor_calls_file_read_successfully():
    ws = WorldState()
    executor = StatefulExecutor(create_default_tool_registry())
    executor.execute("file.write", ws, {"file_id": "doc1", "content": "hello"})

    record = executor.execute("file.read", ws, {"file_id": "doc1"})

    assert record.success is True
    assert record.state_changed is False
    assert record.hash_changed is False
    assert record.observation["content"] == "hello"


def test_executor_completes_write_index_query_loop():
    ws = WorldState()
    executor = StatefulExecutor(create_default_tool_registry())

    write_record = executor.execute("file.write", ws, {"file_id": "doc1", "content": "alpha beta"})
    index_record = executor.execute("search.index", ws, {"file_id": "doc1"})
    query_record = executor.execute("search.query", ws, {"query": "alpha"})

    assert write_record.success is True
    assert index_record.success is True
    assert query_record.success is True
    assert len(query_record.observation["hits"]) == 1
    assert query_record.observation["hits"][0]["file_id"] == "doc1"


def test_executor_returns_failure_for_missing_tool():
    ws = WorldState()
    executor = StatefulExecutor(create_default_tool_registry())

    record = executor.execute("missing.tool", ws, {"x": 1})

    assert record.success is False
    assert record.state_changed is False
    assert record.hash_changed is False
    assert "Tool not found" in record.error
    assert record.pre_state_hash == record.post_state_hash


def test_read_only_tools_do_not_change_hash():
    ws = WorldState()
    executor = StatefulExecutor(create_default_tool_registry())
    executor.execute("file.write", ws, {"file_id": "doc1", "content": "alpha beta"})
    executor.execute("search.index", ws, {"file_id": "doc1"})

    read_record = executor.execute("file.read", ws, {"file_id": "doc1"})
    query_record = executor.execute("search.query", ws, {"query": "alpha"})

    assert read_record.hash_changed is False
    assert query_record.hash_changed is False
    assert read_record.pre_state_hash == read_record.post_state_hash
    assert query_record.pre_state_hash == query_record.post_state_hash


def test_write_tools_change_hash():
    ws = WorldState()
    executor = StatefulExecutor(create_default_tool_registry())

    write_record = executor.execute("file.write", ws, {"file_id": "doc1", "content": "alpha beta"})
    index_record = executor.execute("search.index", ws, {"file_id": "doc1"})

    assert write_record.hash_changed is True
    assert index_record.hash_changed is True
    assert write_record.pre_state_hash != write_record.post_state_hash
    assert index_record.pre_state_hash != index_record.post_state_hash


def test_executor_catches_tool_exception():
    ws = WorldState()
    tools = create_default_tool_registry()
    tools["test.explode"] = ExplodingTool()
    executor = StatefulExecutor(tools)

    record = executor.execute("test.explode", ws, {})

    assert record.success is False
    assert record.state_changed is False
    assert "boom" in record.error


def run_all_tests() -> None:
    test_executor_calls_file_write_successfully()
    test_executor_calls_file_read_successfully()
    test_executor_completes_write_index_query_loop()
    test_executor_returns_failure_for_missing_tool()
    test_read_only_tools_do_not_change_hash()
    test_write_tools_change_hash()
    test_executor_catches_tool_exception()
    print("All stateful_executor tests passed!")


if __name__ == "__main__":
    run_all_tests()
