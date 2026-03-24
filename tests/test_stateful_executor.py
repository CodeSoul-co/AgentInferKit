"""
Unit tests for toolsim.stateful_executor.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toolsim.core.tool_spec import ToolExecutionResult, ToolMetadata, ToolSpec
from toolsim.execution.stateful_executor import ExecutorConfig, StatefulExecutor, create_default_tool_registry
from toolsim.core.world_state import PendingEffect, WorldState


class ExplodingTool(ToolSpec):
    tool_name = "test.explode"
    description = "Raise an exception to test executor error handling."
    input_schema = {"type": "object", "properties": {}}

    def execute(self, state: WorldState, args: dict) -> ToolExecutionResult:
        raise RuntimeError("boom")


class PartialPendingTool(ToolSpec):
    metadata = ToolMetadata(
        name="test.partial_pending",
        domain="test",
        required_permissions=["test.partial_pending"],
        supports_partial=True,
        supports_async=True,
    )

    def execute(self, state: WorldState, args: dict) -> ToolExecutionResult:
        effect = PendingEffect(
            effect_id="eff_demo",
            kind="delayed.index",
            scheduled_at=state.now(),
            execute_after=state.now() + 5,
            payload={"file_id": "doc1"},
        )
        state.schedule_effect(effect)
        return ToolExecutionResult(
            success=True,
            partial=True,
            pending=True,
            state_changed=True,
            scheduled_effects=[effect.to_dict()],
            observation={"scheduled": True},
        )


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


def test_executor_enforces_permissions_when_provided():
    ws = WorldState()
    executor = StatefulExecutor(create_default_tool_registry())

    record = executor.execute("file.write", ws, {"file_id": "doc1", "content": "hello"}, permissions=set())

    assert record.success is False
    assert any(not result.passed for result in record.permission_results)
    assert ws.get_entity("file", "doc1") is None


def test_executor_enforces_preconditions_before_read():
    ws = WorldState()
    executor = StatefulExecutor(create_default_tool_registry())

    record = executor.execute("file.read", ws, {"file_id": "missing"})

    assert record.success is False
    assert any(not result.passed for result in record.precondition_results)
    assert "File must exist before read" in record.error


def test_executor_records_partial_pending_and_scheduled_effects():
    ws = WorldState()
    tools = create_default_tool_registry()
    tools["test.partial_pending"] = PartialPendingTool()
    executor = StatefulExecutor(tools)

    record = executor.execute("test.partial_pending", ws, {}, permissions={"test.partial_pending"})

    assert record.success is True
    assert record.status == "pending"
    assert record.partial is True
    assert record.async_pending is True
    assert record.scheduled_effect_ids == ["eff_demo"]
    assert len(ws.pending_effects) == 1


def test_executor_can_disable_strict_preconditions():
    ws = WorldState()
    executor = StatefulExecutor(create_default_tool_registry(), config=ExecutorConfig(strict_preconditions=False))

    record = executor.execute("file.read", ws, {"file_id": "missing"})

    assert record.success is False
    assert any(not result.passed for result in record.precondition_results)
    assert "File not found" in (record.error or "")


def run_all_tests() -> None:
    test_executor_calls_file_write_successfully()
    test_executor_calls_file_read_successfully()
    test_executor_completes_write_index_query_loop()
    test_executor_returns_failure_for_missing_tool()
    test_read_only_tools_do_not_change_hash()
    test_write_tools_change_hash()
    test_executor_catches_tool_exception()
    test_executor_enforces_permissions_when_provided()
    test_executor_enforces_preconditions_before_read()
    test_executor_records_partial_pending_and_scheduled_effects()
    test_executor_can_disable_strict_preconditions()
    print("All stateful_executor tests passed!")


if __name__ == "__main__":
    run_all_tests()
