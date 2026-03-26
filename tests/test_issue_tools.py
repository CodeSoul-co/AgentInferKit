"""Unit tests for the issue tracker domain tools."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toolsim.backends.sandbox_backend import SandboxBackend
from toolsim.execution.stateful_executor import StatefulExecutor, create_default_tool_registry
from toolsim.runners.experiment_runner import ExperimentRunner
from toolsim.core.world_state import WorldState


def _executor() -> StatefulExecutor:
    return StatefulExecutor(create_default_tool_registry())


def _create_issue(executor: StatefulExecutor, state: WorldState, **overrides):
    args = {
        "issue_id": "iss1",
        "title": "Bug in search flow",
        "description": "Query returns stale hit",
        "reporter": "alice",
        "labels": ["bug"],
    }
    args.update(overrides)
    return executor.execute("issue.create", state, args, permissions={"issue.create"})


def test_issue_create_success():
    state = WorldState()
    record = _create_issue(_executor(), state)

    assert record.success is True
    assert state.get_entity("issue", "iss1")["status"] == "open"
    assert record.observation["created"] is True


def test_issue_duplicate_create_fails():
    executor = _executor()
    state = WorldState()
    _create_issue(executor, state)

    record = executor.execute(
        "issue.create",
        state,
        {"issue_id": "iss1", "title": "Duplicate"},
        permissions={"issue.create"},
    )

    assert record.success is False
    assert any(not result.passed for result in record.precondition_results)


def test_issue_assign_moves_issue_to_in_progress():
    executor = _executor()
    state = WorldState()
    _create_issue(executor, state)

    record = executor.execute(
        "issue.assign",
        state,
        {"issue_id": "iss1", "assignee": "bob"},
        permissions={"issue.assign"},
    )

    assert record.success is True
    issue = state.get_entity("issue", "iss1")
    assert issue["assignee"] == "bob"
    assert issue["status"] == "in_progress"


def test_issue_assign_missing_issue_fails():
    record = _executor().execute(
        "issue.assign",
        WorldState(),
        {"issue_id": "missing", "assignee": "bob"},
        permissions={"issue.assign"},
    )

    assert record.success is False
    assert "Issue must exist before assignment" in [result.message for result in record.precondition_results]


def test_issue_comment_creates_comment_and_updates_count():
    executor = _executor()
    state = WorldState(clock=3.0)
    _create_issue(executor, state)

    record = executor.execute(
        "issue.comment",
        state,
        {"issue_id": "iss1", "comment_id": "c1", "author": "alice", "content": "Investigating now"},
        permissions={"issue.comment"},
    )

    assert record.success is True
    assert state.get_entity("issue_comment", "c1")["content"] == "Investigating now"
    assert state.get_entity("issue", "iss1")["comment_count"] == 1


def test_issue_comment_on_closed_issue_respects_policy():
    executor = _executor()
    state = WorldState(policies={"issue": {"allow_comment_on_closed": False}})
    _create_issue(executor, state)
    executor.execute("issue.assign", state, {"issue_id": "iss1", "assignee": "bob"}, permissions={"issue.assign"})
    executor.execute("issue.close", state, {"issue_id": "iss1", "resolution": "fixed"}, permissions={"issue.close"})

    record = executor.execute(
        "issue.comment",
        state,
        {"issue_id": "iss1", "comment_id": "c2", "content": "Post-close note"},
        permissions={"issue.comment"},
    )

    assert record.success is False
    assert "commenting on a closed issue" in (record.error or "")


def test_issue_close_requires_assignee_by_default():
    executor = _executor()
    state = WorldState()
    _create_issue(executor, state)

    record = executor.execute(
        "issue.close",
        state,
        {"issue_id": "iss1", "resolution": "fixed"},
        permissions={"issue.close"},
    )

    assert record.success is False
    assert "requires an assignee" in (record.error or "")


def test_issue_close_and_reopen_success():
    executor = _executor()
    state = WorldState(clock=5.0)
    _create_issue(executor, state)
    executor.execute("issue.assign", state, {"issue_id": "iss1", "assignee": "bob"}, permissions={"issue.assign"})

    close_record = executor.execute(
        "issue.close",
        state,
        {"issue_id": "iss1", "resolution": "fixed"},
        permissions={"issue.close"},
    )
    reopen_record = executor.execute(
        "issue.reopen",
        state,
        {"issue_id": "iss1", "reason": "Regression still present"},
        permissions={"issue.reopen"},
    )

    assert close_record.success is True
    assert reopen_record.success is True
    assert state.get_entity("issue", "iss1")["status"] == "open"


def test_issue_reopen_non_closed_issue_fails():
    executor = _executor()
    state = WorldState()
    _create_issue(executor, state)

    record = executor.execute(
        "issue.reopen",
        state,
        {"issue_id": "iss1"},
        permissions={"issue.reopen"},
    )

    assert record.success is False
    assert "Only closed issues can be reopened" in (record.error or "")


def test_issue_permission_failure_is_reported():
    executor = _executor()
    state = WorldState()

    record = executor.execute("issue.create", state, {"issue_id": "iss1", "title": "Bug"}, permissions=set())

    assert record.success is False
    assert any(not result.passed for result in record.permission_results)


def test_issue_tools_are_in_default_registry():
    tools = create_default_tool_registry()
    assert "issue.create" in tools
    assert "issue.assign" in tools
    assert "issue.comment" in tools
    assert "issue.close" in tools
    assert "issue.reopen" in tools


def test_experiment_runner_can_run_issue_flow_with_sandbox_backend():
    backend = SandboxBackend(session_id="issue_box")
    runner = ExperimentRunner(backend=backend)
    result = runner.run(
        tool_calls=[
            {"tool_name": "issue.create", "args": {"issue_id": "iss1", "title": "Sandbox bug"}},
            {"tool_name": "issue.assign", "args": {"issue_id": "iss1", "assignee": "bob"}},
            {"tool_name": "issue.close", "args": {"issue_id": "iss1", "resolution": "fixed"}},
        ],
        goals=[
            {"type": "issue_exists", "issue_id": "iss1"},
            {"type": "issue_status_is", "issue_id": "iss1", "status": "closed"},
            {"type": "issue_has_assignee", "issue_id": "iss1", "assignee": "bob"},
        ],
        permissions={"issue.create", "issue.assign", "issue.close"},
        backend=backend,
    )

    assert result.trace[0].backend_name == "sandbox"
    assert result.final_state.resources["sandbox_session"] == "issue_box"
    assert result.state_metrics is not None
    assert result.state_metrics.all_passed is True
