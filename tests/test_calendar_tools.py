"""Unit tests for the calendar domain tools."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toolsim.core.environment import ToolEnvironment
from toolsim.execution.stateful_executor import StatefulExecutor, create_default_tool_registry
from toolsim.core.world_state import WorldState


def _executor() -> StatefulExecutor:
    return StatefulExecutor(create_default_tool_registry())


def _create_baseline_event(executor: StatefulExecutor, state: WorldState, **overrides):
    args = {
        "event_id": "evt1",
        "title": "Team Sync",
        "start_time": 10.0,
        "end_time": 11.0,
        "participants": ["alice", "bob"],
        "location": "Room A",
    }
    args.update(overrides)
    return executor.execute("calendar.create_event", state, args)


def test_calendar_create_event_success():
    state = WorldState()
    record = _create_baseline_event(_executor(), state, permissions={"calendar.create_event"})

    assert record.success is True
    assert state.get_entity("calendar_event", "evt1")["title"] == "Team Sync"
    assert record.observation["created"] is True


def test_calendar_duplicate_event_id_fails():
    executor = _executor()
    state = WorldState()
    _create_baseline_event(executor, state, permissions={"calendar.create_event"})

    record = executor.execute(
        "calendar.create_event",
        state,
        {
            "event_id": "evt1",
            "title": "Conflict",
            "start_time": 12.0,
            "end_time": 13.0,
            "participants": ["carol"],
        },
        permissions={"calendar.create_event"},
    )

    assert record.success is False
    assert any(not result.passed for result in record.precondition_results)


def test_calendar_create_event_rejects_invalid_time_range():
    state = WorldState()
    record = _executor().execute(
        "calendar.create_event",
        state,
        {"event_id": "evt1", "title": "Bad", "start_time": 12.0, "end_time": 12.0, "participants": ["alice"]},
        permissions={"calendar.create_event"},
    )

    assert record.success is False
    assert "start_time must be less than end_time" in (record.error or "")


def test_calendar_conflict_detection_blocks_overlapping_participant_event():
    executor = _executor()
    state = WorldState()
    _create_baseline_event(executor, state, permissions={"calendar.create_event"})

    record = executor.execute(
        "calendar.create_event",
        state,
        {"event_id": "evt2", "title": "1:1", "start_time": 10.5, "end_time": 11.5, "participants": ["bob"]},
        permissions={"calendar.create_event"},
    )

    assert record.success is False
    assert record.observation["conflict_detected"] is True
    assert len(record.observation["conflicts"]) == 1


def test_calendar_search_finds_matching_event():
    executor = _executor()
    state = WorldState()
    _create_baseline_event(executor, state, permissions={"calendar.create_event"})

    record = executor.execute(
        "calendar.search_events",
        state,
        {"participant": "alice", "start_time": 9.0, "end_time": 12.0},
        permissions={"calendar.search_events"},
    )

    assert record.success is True
    assert record.observation["count"] == 1
    assert record.observation["hits"][0]["event_id"] == "evt1"


def test_calendar_update_event_successfully_changes_fields():
    executor = _executor()
    state = WorldState(clock=5.0)
    _create_baseline_event(executor, state, permissions={"calendar.create_event"})
    state.set_clock(6.0)

    record = executor.execute(
        "calendar.update_event",
        state,
        {"event_id": "evt1", "title": "Updated Sync", "end_time": 11.5},
        permissions={"calendar.update_event"},
    )

    assert record.success is True
    event = state.get_entity("calendar_event", "evt1")
    assert event["title"] == "Updated Sync"
    assert event["end_time"] == 11.5
    assert event["updated_at"] == 6.0


def test_calendar_update_event_rejects_conflict():
    executor = _executor()
    state = WorldState()
    _create_baseline_event(executor, state, permissions={"calendar.create_event"})
    executor.execute(
        "calendar.create_event",
        state,
        {"event_id": "evt2", "title": "Design Review", "start_time": 12.0, "end_time": 13.0, "participants": ["alice"]},
        permissions={"calendar.create_event"},
    )

    record = executor.execute(
        "calendar.update_event",
        state,
        {"event_id": "evt2", "start_time": 10.5, "end_time": 10.75},
        permissions={"calendar.update_event"},
    )

    assert record.success is False
    assert record.observation["conflict_detected"] is True


def test_calendar_delete_event_soft_deletes():
    executor = _executor()
    state = WorldState(clock=0.0, policies={"calendar": {"allow_delete_started_event": True}})
    _create_baseline_event(executor, state, permissions={"calendar.create_event"})

    record = executor.execute(
        "calendar.delete_event",
        state,
        {"event_id": "evt1"},
        permissions={"calendar.delete_event"},
    )

    assert record.success is True
    assert state.get_entity("calendar_event", "evt1")["status"] == "cancelled"


def test_calendar_delete_started_event_respects_policy_and_clock():
    executor = _executor()
    state = WorldState(clock=9.0, policies={"calendar": {"allow_delete_started_event": False}})
    _create_baseline_event(executor, state, permissions={"calendar.create_event"})
    env = ToolEnvironment(state=state)
    env.advance_time(1.5)

    record = executor.execute(
        "calendar.delete_event",
        state,
        {"event_id": "evt1"},
        permissions={"calendar.delete_event"},
        environment=env,
    )

    assert state.now() == 10.5
    assert record.success is False
    assert "already started" in (record.error or "")


def test_calendar_tools_are_in_default_registry():
    tools = create_default_tool_registry()
    assert "calendar.create_event" in tools
    assert "calendar.search_events" in tools
    assert "calendar.update_event" in tools
    assert "calendar.delete_event" in tools
