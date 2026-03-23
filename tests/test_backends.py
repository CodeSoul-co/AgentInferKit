"""Unit tests for toolsim backend abstractions."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toolsim.backends.mock_backend import MockBackend
from toolsim.backends.sandbox_backend import SandboxBackend
from toolsim.environment import ToolEnvironment
from toolsim.stateful_executor import StatefulExecutor, create_default_tool_registry
from toolsim.world_state import PendingEffect


def test_mock_backend_basic_crud_and_snapshot_roundtrip():
    backend = MockBackend()
    state = backend.create_state()

    backend.set_entity(state, "file", "f1", {"content": "hello"})
    snapshot_id = backend.snapshot_state(state, label="before-delete")
    backend.delete_entity(state, "file", "f1")
    rolled_back = backend.rollback_state(state, snapshot_id)

    assert backend.get_backend_name() == "mock"
    assert rolled_back is True
    assert backend.get_entity(state, "file", "f1")["content"] == "hello"


def test_sandbox_backend_creates_isolated_state_with_session_metadata():
    backend_a = SandboxBackend(session_id="sandbox_a")
    backend_b = SandboxBackend(session_id="sandbox_b")
    state_a = backend_a.create_state()
    state_b = backend_b.create_state()

    backend_a.set_entity(state_a, "calendar_event", "evt1", {"title": "A"})

    assert backend_a.get_backend_name() == "sandbox"
    assert state_a.resources["sandbox_session"] == "sandbox_a"
    assert state_b.resources["sandbox_session"] == "sandbox_b"
    assert backend_b.get_entity(state_b, "calendar_event", "evt1") is None


def test_backend_schedule_effect_compatibility():
    backend = MockBackend()
    state = backend.create_state()
    backend.schedule_effect(state, PendingEffect(effect_id="eff1", kind="search.reindex_file_snapshot", scheduled_at=0.0, execute_after=1.0, payload={"file_id": "f1"}))

    pending = backend.list_pending_effects(state)

    assert len(pending) == 1
    assert pending[0].effect_id == "eff1"


def test_environment_uses_explicit_backend_for_snapshot_and_rollback():
    backend = SandboxBackend(session_id="sandbox_env")
    state = backend.create_state()
    env = ToolEnvironment(state=state, backend=backend)

    backend.set_entity(state, "file", "f1", {"content": "alpha"})
    snapshot_id = env.snapshot("sandbox-snap")
    backend.set_entity(state, "file", "f1", {"content": "beta"})
    rolled_back = env.rollback(snapshot_id)

    assert rolled_back is True
    assert state.get_entity("file", "f1")["content"] == "alpha"
    assert state.resources["sandbox_session"] == "sandbox_env"


def test_stateful_executor_reports_backend_name_and_runs_with_mock_backend():
    backend = MockBackend()
    state = backend.create_state()
    executor = StatefulExecutor(create_default_tool_registry(), backend=backend)

    record = executor.execute("file.write", state, {"file_id": "f1", "content": "hello"})

    assert record.success is True
    assert record.backend_name == "mock"
    assert state.get_entity("file", "f1")["content"] == "hello"


def test_stateful_executor_runs_calendar_domain_with_sandbox_backend():
    backend = SandboxBackend(session_id="calendar_box")
    state = backend.create_state()
    env = ToolEnvironment(state=state, backend=backend)
    executor = StatefulExecutor(create_default_tool_registry(), backend=backend)

    create_record = executor.execute(
        "calendar.create_event",
        state,
        {"event_id": "evt1", "title": "Team Sync", "start_time": 10.0, "end_time": 11.0, "participants": ["alice", "bob"]},
        permissions={"calendar.create_event"},
        environment=env,
    )
    search_record = executor.execute(
        "calendar.search_events",
        state,
        {"participant": "alice"},
        permissions={"calendar.search_events"},
        environment=env,
    )

    assert create_record.success is True
    assert create_record.backend_name == "sandbox"
    assert search_record.success is True
    assert search_record.observation["hits"][0]["event_id"] == "evt1"
    assert state.resources["sandbox_session"] == "calendar_box"
