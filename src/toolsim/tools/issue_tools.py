"""Issue tracker domain tools with explicit state transitions and policy checks."""

from __future__ import annotations

from typing import Any

from toolsim.core.tool_spec import (
    PostconditionSpec,
    PreconditionSpec,
    ToolExecutionResult,
    ToolMetadata,
    ToolSpec,
)
from toolsim.core.world_state import WorldState

_ISSUE_ENTITY_TYPE = "issue"
_COMMENT_ENTITY_TYPE = "issue_comment"
_DEFAULT_PROJECT_ID = "default"
_STATUS_OPEN = "open"
_STATUS_IN_PROGRESS = "in_progress"
_STATUS_CLOSED = "closed"


def _issue_policy(state: WorldState) -> dict[str, Any]:
    policy = state.policies.get("issue", {})
    return policy if isinstance(policy, dict) else {}


def _find_issue(state: WorldState, issue_id: str) -> dict[str, Any] | None:
    return state.get_entity(_ISSUE_ENTITY_TYPE, issue_id)


def _find_comment(state: WorldState, comment_id: str) -> dict[str, Any] | None:
    return state.get_entity(_COMMENT_ENTITY_TYPE, comment_id)


def _serialize_issue(issue: dict[str, Any]) -> dict[str, Any]:
    return {
        "issue_id": issue.get("issue_id"),
        "title": issue.get("title"),
        "description": issue.get("description"),
        "reporter": issue.get("reporter"),
        "assignee": issue.get("assignee"),
        "status": issue.get("status"),
        "resolution": issue.get("resolution"),
        "labels": list(issue.get("labels", [])),
        "comment_count": issue.get("comment_count", 0),
        "created_at": issue.get("created_at"),
        "updated_at": issue.get("updated_at"),
        "closed_at": issue.get("closed_at"),
        "project_id": issue.get("project_id", _DEFAULT_PROJECT_ID),
    }


def _ensure_project_writable(policy: dict[str, Any], project_id: str) -> str | None:
    if project_id in set(policy.get("read_only_projects", [])):
        return f"Project is read-only: {project_id}"
    return None


class IssueCreateTool(ToolSpec):
    tool_name = "issue.create"
    description = "Create a new issue in open status."
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "issue_id": {"type": "string"},
            "title": {"type": "string"},
            "description": {"type": "string"},
            "reporter": {"type": "string"},
            "labels": {"type": "array"},
            "project_id": {"type": "string"},
        },
        "required": ["issue_id", "title"],
    }
    metadata = ToolMetadata(
        name=tool_name,
        version="0.1",
        domain="issue",
        description=description,
        input_schema=input_schema,
        required_permissions=["issue.create"],
        idempotency="non_idempotent",
    )
    preconditions = [
        PreconditionSpec(
            kind="entity_absent",
            message="Issue id must be new",
            config={"entity_type": _ISSUE_ENTITY_TYPE, "arg_field": "issue_id"},
        )
    ]
    postconditions = [
        PostconditionSpec(
            kind="entity_exists",
            message="Created issue should exist",
            config={"entity_type": _ISSUE_ENTITY_TYPE, "arg_field": "issue_id"},
        ),
        PostconditionSpec(
            kind="entity_field_equals",
            message="Created issue should be open",
            config={"entity_type": _ISSUE_ENTITY_TYPE, "arg_field": "issue_id", "field": "status", "expected": _STATUS_OPEN},
        ),
    ]

    def execute(self, state_or_context: Any, args: dict[str, Any]) -> ToolExecutionResult:
        state = self.get_state_from_input(state_or_context)
        clock = state_or_context.now() if hasattr(state_or_context, "now") else state.now()

        issue_id = args.get("issue_id")
        title = args.get("title")
        if not issue_id:
            return ToolExecutionResult(success=False, error="Missing required argument: issue_id")
        if not title:
            return ToolExecutionResult(success=False, error="Missing required argument: title")

        project_id = args.get("project_id") or _DEFAULT_PROJECT_ID
        policy = _issue_policy(state)
        write_error = _ensure_project_writable(policy, project_id)
        if write_error is not None:
            return ToolExecutionResult(success=False, error=write_error)

        issue = {
            "issue_id": issue_id,
            "title": title,
            "description": args.get("description"),
            "reporter": args.get("reporter"),
            "assignee": None,
            "status": _STATUS_OPEN,
            "resolution": None,
            "labels": list(args.get("labels") or []),
            "comment_count": 0,
            "created_at": clock,
            "updated_at": clock,
            "closed_at": None,
            "project_id": project_id,
        }
        state.set_entity(_ISSUE_ENTITY_TYPE, issue_id, issue)

        return ToolExecutionResult(
            success=True,
            observation={"issue_id": issue_id, "created": True, "issue": _serialize_issue(issue)},
            state_changed=True,
        )


class IssueAssignTool(ToolSpec):
    tool_name = "issue.assign"
    description = "Assign an issue and transition it to in_progress."
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "issue_id": {"type": "string"},
            "assignee": {"type": "string"},
        },
        "required": ["issue_id", "assignee"],
    }
    metadata = ToolMetadata(
        name=tool_name,
        version="0.1",
        domain="issue",
        description=description,
        input_schema=input_schema,
        required_permissions=["issue.assign"],
        idempotency="non_idempotent",
    )
    preconditions = [
        PreconditionSpec(
            kind="entity_exists",
            message="Issue must exist before assignment",
            config={"entity_type": _ISSUE_ENTITY_TYPE, "arg_field": "issue_id"},
        )
    ]
    postconditions = [
        PostconditionSpec(
            kind="entity_field_equals",
            message="Assigned issue should move to in_progress",
            config={"entity_type": _ISSUE_ENTITY_TYPE, "arg_field": "issue_id", "field": "status", "expected": _STATUS_IN_PROGRESS},
        )
    ]

    def execute(self, state_or_context: Any, args: dict[str, Any]) -> ToolExecutionResult:
        state = self.get_state_from_input(state_or_context)
        clock = state_or_context.now() if hasattr(state_or_context, "now") else state.now()
        issue_id = args.get("issue_id")
        assignee = args.get("assignee")

        if not issue_id:
            return ToolExecutionResult(success=False, error="Missing required argument: issue_id")
        if not assignee:
            return ToolExecutionResult(success=False, error="Missing required argument: assignee")

        issue = _find_issue(state, issue_id)
        if issue is None:
            return ToolExecutionResult(success=False, error=f"Issue not found: {issue_id!r}")
        if issue.get("status") == _STATUS_CLOSED:
            return ToolExecutionResult(success=False, error="Cannot assign a closed issue")

        policy = _issue_policy(state)
        write_error = _ensure_project_writable(policy, issue.get("project_id", _DEFAULT_PROJECT_ID))
        if write_error is not None:
            return ToolExecutionResult(success=False, error=write_error)

        updated = dict(issue)
        updated["assignee"] = assignee
        updated["status"] = _STATUS_IN_PROGRESS
        updated["updated_at"] = clock
        state.set_entity(_ISSUE_ENTITY_TYPE, issue_id, updated)

        return ToolExecutionResult(
            success=True,
            observation={"issue_id": issue_id, "assigned": True, "issue": _serialize_issue(updated)},
            state_changed=True,
        )


class IssueCommentTool(ToolSpec):
    tool_name = "issue.comment"
    description = "Add a comment to an issue and update its metadata."
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "issue_id": {"type": "string"},
            "comment_id": {"type": "string"},
            "author": {"type": "string"},
            "content": {"type": "string"},
        },
        "required": ["issue_id", "comment_id", "content"],
    }
    metadata = ToolMetadata(
        name=tool_name,
        version="0.1",
        domain="issue",
        description=description,
        input_schema=input_schema,
        required_permissions=["issue.comment"],
        idempotency="non_idempotent",
    )
    preconditions = [
        PreconditionSpec(
            kind="entity_exists",
            message="Issue must exist before commenting",
            config={"entity_type": _ISSUE_ENTITY_TYPE, "arg_field": "issue_id"},
        ),
        PreconditionSpec(
            kind="entity_absent",
            message="Comment id must be new",
            config={"entity_type": _COMMENT_ENTITY_TYPE, "arg_field": "comment_id"},
        ),
    ]

    def execute(self, state_or_context: Any, args: dict[str, Any]) -> ToolExecutionResult:
        state = self.get_state_from_input(state_or_context)
        clock = state_or_context.now() if hasattr(state_or_context, "now") else state.now()
        issue_id = args.get("issue_id")
        comment_id = args.get("comment_id")
        content = args.get("content")

        if not issue_id:
            return ToolExecutionResult(success=False, error="Missing required argument: issue_id")
        if not comment_id:
            return ToolExecutionResult(success=False, error="Missing required argument: comment_id")
        if not content:
            return ToolExecutionResult(success=False, error="Missing required argument: content")

        issue = _find_issue(state, issue_id)
        if issue is None:
            return ToolExecutionResult(success=False, error=f"Issue not found: {issue_id!r}")
        if _find_comment(state, comment_id) is not None:
            return ToolExecutionResult(success=False, error=f"Comment already exists: {comment_id!r}")

        policy = _issue_policy(state)
        if issue.get("status") == _STATUS_CLOSED and not bool(policy.get("allow_comment_on_closed", True)):
            return ToolExecutionResult(success=False, error="Policy forbids commenting on a closed issue")
        write_error = _ensure_project_writable(policy, issue.get("project_id", _DEFAULT_PROJECT_ID))
        if write_error is not None:
            return ToolExecutionResult(success=False, error=write_error)

        comment = {
            "comment_id": comment_id,
            "issue_id": issue_id,
            "author": args.get("author"),
            "content": content,
            "created_at": clock,
        }
        state.set_entity(_COMMENT_ENTITY_TYPE, comment_id, comment)

        updated = dict(issue)
        updated["comment_count"] = int(updated.get("comment_count", 0)) + 1
        updated["updated_at"] = clock
        state.set_entity(_ISSUE_ENTITY_TYPE, issue_id, updated)

        return ToolExecutionResult(
            success=True,
            observation={"issue_id": issue_id, "comment_id": comment_id, "commented": True, "issue": _serialize_issue(updated)},
            state_changed=True,
        )


class IssueCloseTool(ToolSpec):
    tool_name = "issue.close"
    description = "Close an issue when policy and workflow conditions are satisfied."
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "issue_id": {"type": "string"},
            "resolution": {"type": "string"},
        },
        "required": ["issue_id", "resolution"],
    }
    metadata = ToolMetadata(
        name=tool_name,
        version="0.1",
        domain="issue",
        description=description,
        input_schema=input_schema,
        required_permissions=["issue.close"],
        idempotency="non_idempotent",
    )
    preconditions = [
        PreconditionSpec(
            kind="entity_exists",
            message="Issue must exist before closing",
            config={"entity_type": _ISSUE_ENTITY_TYPE, "arg_field": "issue_id"},
        )
    ]
    postconditions = [
        PostconditionSpec(
            kind="entity_field_equals",
            message="Closed issue should have closed status",
            config={"entity_type": _ISSUE_ENTITY_TYPE, "arg_field": "issue_id", "field": "status", "expected": _STATUS_CLOSED},
        )
    ]

    def execute(self, state_or_context: Any, args: dict[str, Any]) -> ToolExecutionResult:
        state = self.get_state_from_input(state_or_context)
        clock = state_or_context.now() if hasattr(state_or_context, "now") else state.now()
        issue_id = args.get("issue_id")
        resolution = args.get("resolution")

        if not issue_id:
            return ToolExecutionResult(success=False, error="Missing required argument: issue_id")
        if not resolution:
            return ToolExecutionResult(success=False, error="Missing required argument: resolution")

        issue = _find_issue(state, issue_id)
        if issue is None:
            return ToolExecutionResult(success=False, error=f"Issue not found: {issue_id!r}")
        if issue.get("status") == _STATUS_CLOSED:
            return ToolExecutionResult(success=False, error="Issue is already closed")

        policy = _issue_policy(state)
        write_error = _ensure_project_writable(policy, issue.get("project_id", _DEFAULT_PROJECT_ID))
        if write_error is not None:
            return ToolExecutionResult(success=False, error=write_error)
        if bool(policy.get("require_assignee_before_close", True)) and not issue.get("assignee"):
            return ToolExecutionResult(success=False, error="Policy requires an assignee before closing the issue")

        updated = dict(issue)
        updated["status"] = _STATUS_CLOSED
        updated["resolution"] = resolution
        updated["closed_at"] = clock
        updated["updated_at"] = clock
        state.set_entity(_ISSUE_ENTITY_TYPE, issue_id, updated)

        return ToolExecutionResult(
            success=True,
            observation={"issue_id": issue_id, "closed": True, "issue": _serialize_issue(updated)},
            state_changed=True,
        )


class IssueReopenTool(ToolSpec):
    tool_name = "issue.reopen"
    description = "Reopen a closed issue."
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "issue_id": {"type": "string"},
            "reason": {"type": "string"},
        },
        "required": ["issue_id"],
    }
    metadata = ToolMetadata(
        name=tool_name,
        version="0.1",
        domain="issue",
        description=description,
        input_schema=input_schema,
        required_permissions=["issue.reopen"],
        idempotency="non_idempotent",
    )
    preconditions = [
        PreconditionSpec(
            kind="entity_exists",
            message="Issue must exist before reopening",
            config={"entity_type": _ISSUE_ENTITY_TYPE, "arg_field": "issue_id"},
        )
    ]
    postconditions = [
        PostconditionSpec(
            kind="entity_field_equals",
            message="Reopened issue should return to open status",
            config={"entity_type": _ISSUE_ENTITY_TYPE, "arg_field": "issue_id", "field": "status", "expected": _STATUS_OPEN},
        )
    ]

    def execute(self, state_or_context: Any, args: dict[str, Any]) -> ToolExecutionResult:
        state = self.get_state_from_input(state_or_context)
        clock = state_or_context.now() if hasattr(state_or_context, "now") else state.now()
        issue_id = args.get("issue_id")

        if not issue_id:
            return ToolExecutionResult(success=False, error="Missing required argument: issue_id")

        issue = _find_issue(state, issue_id)
        if issue is None:
            return ToolExecutionResult(success=False, error=f"Issue not found: {issue_id!r}")
        if issue.get("status") != _STATUS_CLOSED:
            return ToolExecutionResult(success=False, error="Only closed issues can be reopened")

        policy = _issue_policy(state)
        if not bool(policy.get("allow_reopen_closed", True)):
            return ToolExecutionResult(success=False, error="Policy forbids reopening closed issues")
        write_error = _ensure_project_writable(policy, issue.get("project_id", _DEFAULT_PROJECT_ID))
        if write_error is not None:
            return ToolExecutionResult(success=False, error=write_error)

        updated = dict(issue)
        updated["status"] = _STATUS_OPEN
        updated["updated_at"] = clock
        state.set_entity(_ISSUE_ENTITY_TYPE, issue_id, updated)

        return ToolExecutionResult(
            success=True,
            observation={"issue_id": issue_id, "reopened": True, "reason": args.get("reason"), "issue": _serialize_issue(updated)},
            state_changed=True,
        )


ISSUE_TOOLS: dict[str, ToolSpec] = {
    tool.tool_name: tool
    for tool in [
        IssueCreateTool(),
        IssueAssignTool(),
        IssueCommentTool(),
        IssueCloseTool(),
        IssueReopenTool(),
    ]
}
