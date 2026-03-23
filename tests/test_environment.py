"""Unit tests for Phase 2 environment and side effects."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toolsim.environment import ToolEnvironment
from toolsim.side_effects import SideEffectScheduler, create_default_scheduler
from toolsim.stateful_executor import StatefulExecutor, create_default_tool_registry
from toolsim.world_state import PendingEffect, WorldState


def test_scheduler_applies_ready_effect():
    ws = WorldState(clock=5.0)
    ws.set_entity("file", "f1", {"content": "hello world", "metadata": {}, "revision": 1})
    ws.schedule_effect(PendingEffect(effect_id="eff1", kind="search.reindex_file_snapshot", scheduled_at=0.0, execute_after=3.0, payload={"file_id": "f1"}))

    results = create_default_scheduler().apply_ready_effects(ws)

    assert len(results) == 1
    assert results[0].applied is True
    assert ws.get_entity("search_index", "f1")["indexed_content_snapshot"] == "hello world"
    assert ws.get_pending_effect("eff1").status == "applied"


def test_scheduler_does_not_apply_not_ready_effect():
    ws = WorldState(clock=1.0)
    ws.set_entity("file", "f1", {"content": "hello world", "metadata": {}, "revision": 1})
    ws.schedule_effect(PendingEffect(effect_id="eff1", kind="search.reindex_file_snapshot", scheduled_at=0.0, execute_after=3.0, payload={"file_id": "f1"}))

    results = create_default_scheduler().apply_ready_effects(ws)

    assert results == []
    assert ws.get_entity("search_index", "f1") is None
    assert ws.get_pending_effect("eff1").status == "pending"


def test_scheduler_marks_unknown_handler_failed():
    ws = WorldState(clock=5.0)
    ws.schedule_effect(PendingEffect(effect_id="eff_unknown", kind="unknown.effect", scheduled_at=0.0, execute_after=0.0, payload={}))

    results = SideEffectScheduler().apply_ready_effects(ws)

    assert len(results) == 1
    assert results[0].applied is False
    assert "No handler registered" in (results[0].error or "")
    assert ws.get_pending_effect("eff_unknown").status == "failed"


def test_environment_advance_time_applies_ready_effects():
    ws = WorldState(clock=0.0)
    ws.set_entity("file", "f1", {"content": "alpha", "metadata": {}, "revision": 1})
    ws.schedule_effect(PendingEffect(effect_id="eff1", kind="search.reindex_file_snapshot", scheduled_at=0.0, execute_after=2.0, payload={"file_id": "f1"}))
    env = ToolEnvironment(state=ws)

    results = env.advance_time(2.0)

    assert ws.now() == 2.0
    assert len(results) == 1
    assert results[0].applied is True
    assert ws.get_entity("search_index", "f1") is not None


def test_executor_delayed_reindex_flow_requires_time_advance():
    ws = WorldState()
    env = ToolEnvironment(state=ws, auto_apply_ready_effects=True)
    executor = StatefulExecutor(create_default_tool_registry())

    write_record = executor.execute(
        "file.write",
        ws,
        {"file_id": "f1", "content": "gamma signal", "schedule_search_reindex": True, "reindex_delay": 2.0},
        environment=env,
    )
    early_query = executor.execute("search.query", ws, {"query": "gamma"}, environment=env)
    applied = env.advance_time(2.0)
    late_query = executor.execute("search.query", ws, {"query": "gamma"}, environment=env)

    assert write_record.async_pending is True
    assert write_record.scheduled_effect_ids == ["eff_reindex_f1_1"]
    assert early_query.observation["hits"] == []
    assert len(applied) == 1
    assert applied[0].applied is True
    assert len(late_query.observation["hits"]) == 1
    assert late_query.observation["hits"][0]["file_id"] == "f1"


def test_executor_record_includes_applied_effect_ids_when_effect_ready_immediately():
    ws = WorldState()
    env = ToolEnvironment(state=ws)
    executor = StatefulExecutor(create_default_tool_registry())

    record = executor.execute(
        "file.write",
        ws,
        {"file_id": "f1", "content": "instant", "schedule_search_reindex": True, "reindex_delay": 0.0},
        environment=env,
    )

    assert record.scheduled_effect_ids == ["eff_reindex_f1_1"]
    assert record.applied_effect_ids == ["eff_reindex_f1_1"]
    assert record.applied_effect_count == 1
    assert ws.get_entity("search_index", "f1") is not None
