"""Stateless baseline runner.

Semantics:
  - No explicit search_index entities.
  - search.query directly searches current file content via substring matching.
  - Still reuses TraceState as minimal shared storage.
"""

from __future__ import annotations

from typing import Any

from toolsim.core.tool_spec import ToolExecutionResult, ToolSpec
from toolsim.core.trace_state import TraceState
from toolsim.evaluators.evaluator import (
    CallLevelEvaluator,
    StateEvaluationResult,
    StateGoalResult,
    StateLevelEvaluator,
)
from toolsim.execution.stateful_executor import StatefulExecutor
from toolsim.execution.stateful_tracer import TraceRecorder
from toolsim.runners.experiment_runner import ExperimentResult
from toolsim.tools.file_tools import FILE_TOOLS
from toolsim.tools.toolsandbox_tools import TOOLSANDBOX_TOOLS


class StatelessSearchQueryTool(ToolSpec):
    """Search query that directly scans current file entity content via substring matching."""

    tool_name: str = "search.query"
    description: str = (
        "Search current file contents directly using simple substring matching. "
        "No explicit search index is required."
    )
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Substring to search for."},
        },
        "required": ["query"],
    }

    def execute(self, state: TraceState, args: dict[str, Any]) -> ToolExecutionResult:
        query: str | None = args.get("query")

        if not query:
            return ToolExecutionResult(
                success=False,
                error="Missing required argument: query",
                state_changed=False,
            )

        hits: list[dict[str, Any]] = []
        for file_id, file_entity in state.entities.get("file", {}).items():
            content = file_entity.get("content", "")
            if query in content:
                hits.append({
                    "file_id": file_id,
                    "content": content,
                    "metadata": file_entity.get("metadata", {}),
                })

        return ToolExecutionResult(
            success=True,
            observation={
                "tool_name": self.tool_name,
                "query": query,
                "hits": hits,
            },
            state_changed=False,
        )


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
        "project_id": issue.get("project_id", "default"),
    }


def _serialize_event(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_id": event.get("event_id"),
        "title": event.get("title"),
        "start_time": event.get("start_time"),
        "end_time": event.get("end_time"),
        "participants": list(event.get("participants", [])),
        "location": event.get("location"),
        "description": event.get("description"),
        "status": event.get("status"),
        "calendar_id": event.get("calendar_id", "default"),
        "created_at": event.get("created_at"),
        "updated_at": event.get("updated_at"),
    }


class StatelessCalendarCreateEventTool(ToolSpec):
    """Create an event without conflict detection or calendar policy enforcement."""

    tool_name = "calendar.create_event"

    def execute(self, state: TraceState, args: dict[str, Any]) -> ToolExecutionResult:
        event_id = args.get("event_id")
        title = args.get("title")
        if not event_id:
            return ToolExecutionResult(success=False, error="Missing required argument: event_id")
        if not title:
            return ToolExecutionResult(success=False, error="Missing required argument: title")

        try:
            start_time = float(args.get("start_time"))
            end_time = float(args.get("end_time"))
        except (TypeError, ValueError):
            return ToolExecutionResult(success=False, error="start_time and end_time must be numeric")

        event = {
            "event_id": event_id,
            "title": title,
            "start_time": start_time,
            "end_time": end_time,
            "participants": list(args.get("participants") or []),
            "location": args.get("location"),
            "description": args.get("description"),
            "status": "confirmed",
            "calendar_id": args.get("calendar_id", "default"),
            "created_at": state.now(),
            "updated_at": state.now(),
        }
        state.set_entity("calendar_event", event_id, event)
        return ToolExecutionResult(
            success=True,
            observation={"event_id": event_id, "created": True, "event": _serialize_event(event)},
            state_changed=True,
        )


class StatelessCalendarUpdateEventTool(ToolSpec):
    """Update an event directly, ignoring conflict detection and calendar policy checks."""

    tool_name = "calendar.update_event"

    def execute(self, state: TraceState, args: dict[str, Any]) -> ToolExecutionResult:
        event_id = args.get("event_id")
        if not event_id:
            return ToolExecutionResult(success=False, error="Missing required argument: event_id")
        existing = state.get_entity("calendar_event", event_id)
        if existing is None:
            return ToolExecutionResult(success=False, error=f"Event not found: {event_id!r}")

        updated = dict(existing)
        for field in ["title", "location", "description", "status"]:
            if field in args:
                updated[field] = args.get(field)
        if "participants" in args:
            updated["participants"] = list(args.get("participants") or [])
        if "start_time" in args:
            updated["start_time"] = float(args.get("start_time"))
        if "end_time" in args:
            updated["end_time"] = float(args.get("end_time"))
        updated["updated_at"] = state.now()
        state.set_entity("calendar_event", event_id, updated)
        return ToolExecutionResult(
            success=True,
            observation={"event_id": event_id, "updated": True, "event": _serialize_event(updated)},
            state_changed=True,
        )


class StatelessCalendarSearchEventsTool(ToolSpec):
    """Search current calendar events directly."""

    tool_name = "calendar.search_events"

    def execute(self, state: TraceState, args: dict[str, Any]) -> ToolExecutionResult:
        start_time = args.get("start_time")
        end_time = args.get("end_time")
        participant = args.get("participant")
        calendar_id = args.get("calendar_id")
        status = args.get("status")
        query = (args.get("query") or "").lower()

        hits: list[dict[str, Any]] = []
        for _, event in sorted(state.entities.get("calendar_event", {}).items()):
            if start_time is not None and float(event.get("end_time", 0.0)) <= float(start_time):
                continue
            if end_time is not None and float(event.get("start_time", 0.0)) >= float(end_time):
                continue
            if participant and participant not in event.get("participants", []):
                continue
            if calendar_id and event.get("calendar_id", "default") != calendar_id:
                continue
            if status and event.get("status") != status:
                continue
            if query:
                haystack = " ".join(str(event.get(key) or "") for key in ["title", "location", "description"]).lower()
                if query not in haystack:
                    continue
            hits.append(_serialize_event(event))

        return ToolExecutionResult(success=True, observation={"hits": hits, "count": len(hits)}, state_changed=False)


class StatelessCalendarDeleteEventTool(ToolSpec):
    """Cancel an event directly without started-event policy checks."""

    tool_name = "calendar.delete_event"

    def execute(self, state: TraceState, args: dict[str, Any]) -> ToolExecutionResult:
        event_id = args.get("event_id")
        if not event_id:
            return ToolExecutionResult(success=False, error="Missing required argument: event_id")
        event = state.get_entity("calendar_event", event_id)
        if event is None:
            return ToolExecutionResult(success=False, error=f"Event not found: {event_id!r}")

        updated = dict(event)
        updated["status"] = "cancelled"
        updated["updated_at"] = state.now()
        state.set_entity("calendar_event", event_id, updated)
        return ToolExecutionResult(
            success=True,
            observation={"event_id": event_id, "deleted": True, "event": _serialize_event(updated)},
            state_changed=True,
        )


class StatelessIssueCreateTool(ToolSpec):
    """Create an issue without workflow metadata or policy enforcement."""

    tool_name = "issue.create"

    def execute(self, state: TraceState, args: dict[str, Any]) -> ToolExecutionResult:
        issue_id = args.get("issue_id")
        title = args.get("title")
        if not issue_id:
            return ToolExecutionResult(success=False, error="Missing required argument: issue_id")
        if not title:
            return ToolExecutionResult(success=False, error="Missing required argument: title")

        issue = {
            "issue_id": issue_id,
            "title": title,
            "description": args.get("description"),
            "reporter": args.get("reporter"),
            "assignee": None,
            "status": "open",
            "resolution": None,
            "labels": list(args.get("labels") or []),
            "comment_count": 0,
            "created_at": state.now(),
            "updated_at": state.now(),
            "closed_at": None,
            "project_id": args.get("project_id", "default"),
        }
        state.set_entity("issue", issue_id, issue)
        return ToolExecutionResult(
            success=True,
            observation={"issue_id": issue_id, "created": True, "issue": _serialize_issue(issue)},
            state_changed=True,
        )


class StatelessIssueAssignTool(ToolSpec):
    """Assign an issue if it exists, with no status transition restrictions."""

    tool_name = "issue.assign"

    def execute(self, state: TraceState, args: dict[str, Any]) -> ToolExecutionResult:
        issue_id = args.get("issue_id")
        assignee = args.get("assignee")
        if not issue_id:
            return ToolExecutionResult(success=False, error="Missing required argument: issue_id")
        if not assignee:
            return ToolExecutionResult(success=False, error="Missing required argument: assignee")

        issue = state.get_entity("issue", issue_id)
        if issue is None:
            return ToolExecutionResult(success=False, error=f"Issue not found: {issue_id!r}")

        updated = dict(issue)
        updated["assignee"] = assignee
        updated["status"] = "in_progress"
        updated["updated_at"] = state.now()
        state.set_entity("issue", issue_id, updated)
        return ToolExecutionResult(
            success=True,
            observation={"issue_id": issue_id, "assigned": True, "issue": _serialize_issue(updated)},
            state_changed=True,
        )


class StatelessIssueCommentTool(ToolSpec):
    """Append a comment without closed-issue policy checks."""

    tool_name = "issue.comment"

    def execute(self, state: TraceState, args: dict[str, Any]) -> ToolExecutionResult:
        issue_id = args.get("issue_id")
        comment_id = args.get("comment_id")
        content = args.get("content")
        if not issue_id:
            return ToolExecutionResult(success=False, error="Missing required argument: issue_id")
        if not comment_id:
            return ToolExecutionResult(success=False, error="Missing required argument: comment_id")
        if not content:
            return ToolExecutionResult(success=False, error="Missing required argument: content")

        issue = state.get_entity("issue", issue_id)
        if issue is None:
            return ToolExecutionResult(success=False, error=f"Issue not found: {issue_id!r}")

        state.set_entity("issue_comment", comment_id, {
            "comment_id": comment_id,
            "issue_id": issue_id,
            "author": args.get("author"),
            "content": content,
            "created_at": state.now(),
        })
        updated = dict(issue)
        updated["comment_count"] = int(updated.get("comment_count", 0)) + 1
        updated["updated_at"] = state.now()
        state.set_entity("issue", issue_id, updated)
        return ToolExecutionResult(
            success=True,
            observation={"issue_id": issue_id, "comment_id": comment_id, "commented": True, "issue": _serialize_issue(updated)},
            state_changed=True,
        )


class StatelessIssueCloseTool(ToolSpec):
    """Close an issue directly; stateless baseline ignores assignee workflow rules."""

    tool_name = "issue.close"

    def execute(self, state: TraceState, args: dict[str, Any]) -> ToolExecutionResult:
        issue_id = args.get("issue_id")
        resolution = args.get("resolution")
        if not issue_id:
            return ToolExecutionResult(success=False, error="Missing required argument: issue_id")
        if not resolution:
            return ToolExecutionResult(success=False, error="Missing required argument: resolution")

        issue = state.get_entity("issue", issue_id)
        if issue is None:
            return ToolExecutionResult(success=False, error=f"Issue not found: {issue_id!r}")

        updated = dict(issue)
        updated["status"] = "closed"
        updated["resolution"] = resolution
        updated["closed_at"] = state.now()
        updated["updated_at"] = state.now()
        state.set_entity("issue", issue_id, updated)
        return ToolExecutionResult(
            success=True,
            observation={"issue_id": issue_id, "closed": True, "issue": _serialize_issue(updated)},
            state_changed=True,
        )


class StatelessIssueReopenTool(ToolSpec):
    """Reopen an issue directly without closed-state validation."""

    tool_name = "issue.reopen"

    def execute(self, state: TraceState, args: dict[str, Any]) -> ToolExecutionResult:
        issue_id = args.get("issue_id")
        if not issue_id:
            return ToolExecutionResult(success=False, error="Missing required argument: issue_id")
        issue = state.get_entity("issue", issue_id)
        if issue is None:
            return ToolExecutionResult(success=False, error=f"Issue not found: {issue_id!r}")

        updated = dict(issue)
        updated["status"] = "open"
        updated["updated_at"] = state.now()
        state.set_entity("issue", issue_id, updated)
        return ToolExecutionResult(
            success=True,
            observation={"issue_id": issue_id, "reopened": True, "reason": args.get("reason"), "issue": _serialize_issue(updated)},
            state_changed=True,
        )


STATELESS_TOOLS: dict[str, ToolSpec] = {
    **FILE_TOOLS,
    "search.query": StatelessSearchQueryTool(),
    "calendar.create_event": StatelessCalendarCreateEventTool(),
    "calendar.update_event": StatelessCalendarUpdateEventTool(),
    "calendar.search_events": StatelessCalendarSearchEventsTool(),
    "calendar.delete_event": StatelessCalendarDeleteEventTool(),
    "issue.create": StatelessIssueCreateTool(),
    "issue.assign": StatelessIssueAssignTool(),
    "issue.comment": StatelessIssueCommentTool(),
    "issue.close": StatelessIssueCloseTool(),
    "issue.reopen": StatelessIssueReopenTool(),
    **TOOLSANDBOX_TOOLS,
}


class StatelessStateLevelEvaluator(StateLevelEvaluator):
    """State-level evaluator aligned with stateless query semantics."""

    def _evaluate_goal(self, state: TraceState, goal: dict[str, Any]) -> StateGoalResult:
        goal_type = goal.get("type", "unknown")

        if goal_type == "indexed_contains":
            return StateGoalResult(
                goal_type=goal_type,
                passed=False,
                message="Goal unsupported in stateless baseline: indexed_contains",
            )

        if goal_type == "query_hits_file":
            query = goal.get("query", "")
            file_id = goal.get("file_id")
            query_result = StatelessSearchQueryTool().execute(state, {"query": query})
            hits = query_result.observation.get("hits", []) if query_result.success else []
            passed = any(hit.get("file_id") == file_id for hit in hits)
            return StateGoalResult(
                goal_type=goal_type,
                passed=passed,
                message=(
                    f"Query {query!r} hit file {file_id}"
                    if passed
                    else f"Query {query!r} did not hit file {file_id}"
                ),
            )

        return super()._evaluate_goal(state, goal)


class StatelessExperimentRunner:
    """Stateless experiment runner with an interface similar to :class:`ExperimentRunner`."""

    def __init__(
        self,
        executor: StatefulExecutor | None = None,
        call_evaluator: CallLevelEvaluator | None = None,
        state_evaluator: StatelessStateLevelEvaluator | None = None,
    ) -> None:
        self._executor = executor
        self._call_evaluator = call_evaluator or CallLevelEvaluator()
        self._state_evaluator = state_evaluator or StatelessStateLevelEvaluator()

    def run(
        self,
        tool_calls: list[dict[str, Any]],
        initial_state: TraceState | None = None,
        goals: list[dict[str, Any]] | None = None,
    ) -> ExperimentResult:
        state = initial_state if initial_state is not None else TraceState()
        tracer = TraceRecorder()
        executor = self._build_executor(tracer)

        for tool_call in tool_calls:
            tool_name = tool_call.get("tool_name", "")
            args = tool_call.get("args", {})
            executor.execute(tool_name, state, args)

        trace = tracer.get_records()
        call_metrics = self._call_evaluator.evaluate(trace)
        state_metrics: StateEvaluationResult | None = (
            self._state_evaluator.evaluate(state, goals) if goals is not None else None
        )

        return ExperimentResult(
            final_state=state,
            trace=trace,
            call_metrics=call_metrics,
            state_metrics=state_metrics,
            all_calls_succeeded=all(record.success for record in trace),
            final_state_hash=state.compute_hash(),
        )

    def _build_executor(self, tracer: TraceRecorder) -> StatefulExecutor:
        if self._executor is not None:
            return StatefulExecutor(self._executor._tools, tracer=tracer)
        return StatefulExecutor(STATELESS_TOOLS, tracer=tracer)
