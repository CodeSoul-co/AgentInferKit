"""Unit tests for toolsim backend abstractions."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toolsim.backends.mock_backend import MockBackend
from toolsim.backends.sandbox_backend import SandboxBackend
from toolsim.backends.live_like_backend import LiveLikeBackend
from toolsim.core.environment import ToolEnvironment
from toolsim.execution.stateful_executor import StatefulExecutor, create_default_tool_registry
from toolsim.core.world_state import PendingEffect


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


def test_live_like_backend_marks_live_like_session_metadata():
    backend = LiveLikeBackend(session_id="live_like_test")
    state = backend.create_state()

    assert backend.get_backend_name() == "live_like"
    assert state.resources["sandbox_session"] == "live_like_test"
    assert state.resources["live_like_session"] == "live_like_test"
    assert state.policies["backend"]["realism"] == "live_like"


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


def test_sandbox_backend_persists_file_and_search_artifacts(tmp_path):
    backend = SandboxBackend(session_id="artifact_box", artifact_root=tmp_path)
    state = backend.create_state()
    env = ToolEnvironment(state=state, backend=backend)
    executor = StatefulExecutor(create_default_tool_registry(), backend=backend)

    write_record = executor.execute(
        "file.write",
        state,
        {"file_id": "notes/alpha", "content": "alpha beta", "metadata": {"owner": "qa"}},
        permissions={"file.write"},
        environment=env,
    )
    read_record = executor.execute(
        "file.read",
        state,
        {"file_id": "notes/alpha"},
        permissions={"file.read"},
        environment=env,
    )
    index_record = executor.execute(
        "search.index",
        state,
        {"file_id": "notes/alpha"},
        permissions={"search.index"},
        environment=env,
    )
    query_record = executor.execute(
        "search.query",
        state,
        {"query": "beta"},
        permissions={"search.query"},
        environment=env,
    )

    file_path = Path(write_record.observation["sandbox_artifact_path"])
    index_path = Path(index_record.observation["sandbox_index_path"])

    assert write_record.success is True
    assert read_record.observation["read_from_artifact"] is True
    assert file_path.exists()
    assert file_path.read_text(encoding="utf-8") == "alpha beta"
    assert "sandbox_artifact_path" not in state.get_entity("file", "notes/alpha")
    assert index_record.success is True
    assert index_path.exists()
    assert "sandbox_index_path" not in state.get_entity("search_index", "notes/alpha")
    assert query_record.success is True
    assert query_record.observation["hits"][0]["file_id"] == "notes/alpha"
    assert query_record.observation["hits"][0]["source"] == "sandbox_index"
