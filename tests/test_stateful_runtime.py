"""Unit tests for the session-aware stateful runtime adapter."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toolsim.adapters.stateful_runtime import StatefulToolRuntime


def test_stateful_runtime_persists_state_within_session():
    runtime = StatefulToolRuntime()

    create = runtime.execute_tool_call(
        "sess1",
        "issue.create",
        {"issue_id": "iss1", "title": "Search bug"},
        permissions={"issue.create"},
    )
    assign = runtime.execute_tool_call(
        "sess1",
        "issue.assign",
        {"issue_id": "iss1", "assignee": "bob"},
        permissions={"issue.assign"},
    )

    assert create.success is True
    assert assign.success is True
    env = runtime.get_environment("sess1")
    assert env is not None
    assert env.state.get_entity("issue", "iss1")["assignee"] == "bob"


def test_stateful_runtime_isolates_sessions():
    runtime = StatefulToolRuntime()
    runtime.execute_tool_call(
        "sess1",
        "issue.create",
        {"issue_id": "iss1", "title": "Search bug"},
        permissions={"issue.create"},
    )
    other = runtime.execute_tool_call(
        "sess2",
        "issue.assign",
        {"issue_id": "iss1", "assignee": "bob"},
        permissions={"issue.assign"},
    )

    assert other.success is False
    assert runtime.get_environment("sess2") is not None
    assert runtime.get_environment("sess2").state.get_entity("issue", "iss1") is None


def test_stateful_runtime_supports_sandbox_backend():
    runtime = StatefulToolRuntime()
    response = runtime.execute_tool_call(
        "sandbox_session",
        "issue.create",
        {"issue_id": "iss1", "title": "Sandbox bug"},
        permissions={"issue.create"},
        backend="sandbox",
    )

    assert response.success is True
    assert response.backend_name == "sandbox"
    env = runtime.get_environment("sandbox_session")
    assert env is not None
    assert env.state.resources["sandbox_session"] == "sandbox_session"


def test_stateful_runtime_can_reset_session():
    runtime = StatefulToolRuntime()
    runtime.execute_tool_call(
        "sess1",
        "issue.create",
        {"issue_id": "iss1", "title": "Search bug"},
        permissions={"issue.create"},
    )

    runtime.reset_session("sess1")

    assert runtime.get_environment("sess1") is None
