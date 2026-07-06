"""
comparison_runner.py — Stateless vs Stateful comparison runner
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from toolsim.adapters.toolsandbox_adapter import ToolSandboxConvertedCase
from toolsim.runners.experiment_runner import ExperimentResult, ExperimentRunner
from toolsim.runners.stateless_baseline import StatelessExperimentRunner
from toolsim.core.utils import extract_last_query_hits
from toolsim.core.world_state import WorldState


@dataclass
class ComparisonCase:
    case_name: str
    description: str
    stateful_tool_calls: list[dict[str, Any]]
    stateless_tool_calls: list[dict[str, Any]]
    goals_stateful: list[dict[str, Any]] | None = None
    goals_stateless: list[dict[str, Any]] | None = None
    initial_state_stateful: WorldState | None = None
    initial_state_stateless: WorldState | None = None


@dataclass
class ComparisonResult:
    case_name: str
    stateful_result: ExperimentResult
    stateless_result: ExperimentResult
    summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_name": self.case_name,
            "stateful_result": self.stateful_result.to_dict(),
            "stateless_result": self.stateless_result.to_dict(),
            "summary": self.summary,
        }

    def to_readable_summary(self) -> dict[str, Any]:
        """Export a compact summary suitable for direct inspection."""
        return {
            "case_name": self.case_name,
            "stateful_trace_length": len(self.stateful_result.trace),
            "stateless_trace_length": len(self.stateless_result.trace),
            "stateful_final_hits": extract_last_query_hits(self.stateful_result.trace),
            "stateless_final_hits": extract_last_query_hits(self.stateless_result.trace),
            "stateful_call_metrics": self.stateful_result.call_metrics.to_dict(),
            "stateless_call_metrics": self.stateless_result.call_metrics.to_dict(),
            "stateful_state_metrics": (
                self.stateful_result.state_metrics.to_dict()
                if self.stateful_result.state_metrics is not None
                else None
            ),
            "stateless_state_metrics": (
                self.stateless_result.state_metrics.to_dict()
                if self.stateless_result.state_metrics is not None
                else None
            ),
            "summary": self.summary,
        }


class ComparisonRunner:
    """Run a single comparison case with both stateful and stateless runners."""

    def __init__(
        self,
        stateful_runner: ExperimentRunner | None = None,
        stateless_runner: StatelessExperimentRunner | None = None,
    ) -> None:
        self._stateful_runner = stateful_runner or ExperimentRunner()
        self._stateless_runner = stateless_runner or StatelessExperimentRunner()

    def run_case(self, case: ComparisonCase) -> ComparisonResult:
        stateful_result = self._stateful_runner.run(
            tool_calls=case.stateful_tool_calls,
            initial_state=_clone_state(case.initial_state_stateful) if case.initial_state_stateful is not None else WorldState(),
            goals=case.goals_stateful,
        )
        stateless_result = self._stateless_runner.run(
            tool_calls=case.stateless_tool_calls,
            initial_state=_clone_state(case.initial_state_stateless) if case.initial_state_stateless is not None else WorldState(),
            goals=case.goals_stateless,
        )

        summary = {
            "stateful_all_calls_succeeded": stateful_result.all_calls_succeeded,
            "stateless_all_calls_succeeded": stateless_result.all_calls_succeeded,
            "stateful_all_goals_passed": (
                stateful_result.state_metrics.all_passed if stateful_result.state_metrics is not None else None
            ),
            "stateless_all_goals_passed": (
                stateless_result.state_metrics.all_passed if stateless_result.state_metrics is not None else None
            ),
        }

        return ComparisonResult(
            case_name=case.case_name,
            stateful_result=stateful_result,
            stateless_result=stateless_result,
            summary=summary,
        )

    def run_cases(self, cases: list[ComparisonCase]) -> list[ComparisonResult]:
        """Run multiple comparison cases sequentially."""
        return [self.run_case(case) for case in cases]

    def run_cases_with_readable_summary(self, cases: list[ComparisonCase]) -> list[dict[str, Any]]:
        """Run multiple comparison cases and return a list of human-readable summaries."""
        return [result.to_readable_summary() for result in self.run_cases(cases)]


def build_stateless_vs_stateful_cases() -> list[ComparisonCase]:
    """Build the default case set highlighting explicit-index dependency differences."""
    return [
        ComparisonCase(
            case_name="write_then_query",
            description="Stateful requires explicit indexing before search can hit; stateless searches current file content directly.",
            stateful_tool_calls=[
                {"tool_name": "file.write", "args": {"file_id": "f1", "content": "hello world"}},
                {"tool_name": "search.query", "args": {"query": "hello"}},
            ],
            stateless_tool_calls=[
                {"tool_name": "file.write", "args": {"file_id": "f1", "content": "hello world"}},
                {"tool_name": "search.query", "args": {"query": "hello"}},
            ],
            goals_stateful=[
                {"type": "entity_exists", "entity_type": "file", "entity_id": "f1"},
            ],
            goals_stateless=[
                {"type": "entity_exists", "entity_type": "file", "entity_id": "f1"},
                {"type": "query_hits_file", "query": "hello", "file_id": "f1"},
            ],
        ),
        ComparisonCase(
            case_name="write_index_query",
            description="Both settings can hit the file, but stateful needs an explicit search.index step.",
            stateful_tool_calls=[
                {"tool_name": "file.write", "args": {"file_id": "f1", "content": "hello world"}},
                {"tool_name": "search.index", "args": {"file_id": "f1"}},
                {"tool_name": "search.query", "args": {"query": "hello"}},
            ],
            stateless_tool_calls=[
                {"tool_name": "file.write", "args": {"file_id": "f1", "content": "hello world"}},
                {"tool_name": "search.query", "args": {"query": "hello"}},
            ],
            goals_stateful=[
                {"type": "entity_exists", "entity_type": "file", "entity_id": "f1"},
                {"type": "indexed_contains", "file_id": "f1", "substring": "hello"},
                {"type": "query_hits_file", "query": "hello", "file_id": "f1"},
            ],
            goals_stateless=[
                {"type": "entity_exists", "entity_type": "file", "entity_id": "f1"},
                {"type": "query_hits_file", "query": "hello", "file_id": "f1"},
            ],
        ),
        ComparisonCase(
            case_name="overwrite_without_reindex",
            description="Stateful search can stay on the stale indexed snapshot, while stateless search reflects the latest file content.",
            stateful_tool_calls=[
                {"tool_name": "file.write", "args": {"file_id": "f1", "content": "old hello"}},
                {"tool_name": "search.index", "args": {"file_id": "f1"}},
                {"tool_name": "file.write", "args": {"file_id": "f1", "content": "new gamma"}},
                {"tool_name": "search.query", "args": {"query": "hello"}},
            ],
            stateless_tool_calls=[
                {"tool_name": "file.write", "args": {"file_id": "f1", "content": "old hello"}},
                {"tool_name": "file.write", "args": {"file_id": "f1", "content": "new gamma"}},
                {"tool_name": "search.query", "args": {"query": "hello"}},
            ],
            goals_stateful=[
                {"type": "query_hits_file", "query": "hello", "file_id": "f1"},
            ],
            goals_stateless=[
                {"type": "entity_field_equals", "entity_type": "file", "entity_id": "f1", "field": "content", "expected": "new gamma"},
            ],
        ),
        ComparisonCase(
            case_name="issue_close_requires_assignment",
            description="Stateful issue closing enforces workflow dependency and recovery; stateless baseline closes directly.",
            stateful_tool_calls=[
                {"tool_name": "issue.create", "args": {"issue_id": "iss1", "title": "Search bug", "reporter": "alice"}},
                {"tool_name": "issue.close", "args": {"issue_id": "iss1", "resolution": "fixed"}},
                {"tool_name": "issue.assign", "args": {"issue_id": "iss1", "assignee": "bob"}},
                {"tool_name": "issue.close", "args": {"issue_id": "iss1", "resolution": "fixed"}},
            ],
            stateless_tool_calls=[
                {"tool_name": "issue.create", "args": {"issue_id": "iss1", "title": "Search bug", "reporter": "alice"}},
                {"tool_name": "issue.close", "args": {"issue_id": "iss1", "resolution": "fixed"}},
            ],
            goals_stateful=[
                {"type": "issue_exists", "issue_id": "iss1"},
                {"type": "issue_status_is", "issue_id": "iss1", "status": "closed"},
                {"type": "issue_has_assignee", "issue_id": "iss1", "assignee": "bob"},
            ],
            goals_stateless=[
                {"type": "issue_exists", "issue_id": "iss1"},
                {"type": "issue_status_is", "issue_id": "iss1", "status": "closed"},
            ],
        ),
        ComparisonCase(
            case_name="multi_file_partial_index",
            description="Stateful search only sees explicitly indexed files; stateless search scans all current file content.",
            stateful_tool_calls=[
                {"tool_name": "file.write", "args": {"file_id": "f1", "content": "alpha one"}},
                {"tool_name": "file.write", "args": {"file_id": "f2", "content": "alpha two"}},
                {"tool_name": "search.index", "args": {"file_id": "f1"}},
                {"tool_name": "search.query", "args": {"query": "alpha"}},
            ],
            stateless_tool_calls=[
                {"tool_name": "file.write", "args": {"file_id": "f1", "content": "alpha one"}},
                {"tool_name": "file.write", "args": {"file_id": "f2", "content": "alpha two"}},
                {"tool_name": "search.query", "args": {"query": "alpha"}},
            ],
            goals_stateful=[
                {"type": "query_hits_file", "query": "alpha", "file_id": "f1"},
            ],
            goals_stateless=[
                {"type": "query_hits_file", "query": "alpha", "file_id": "f1"},
                {"type": "query_hits_file", "query": "alpha", "file_id": "f2"},
            ],
        ),
        ComparisonCase(
            case_name="reindex_after_overwrite",
            description="Stateful search reflects overwritten content only after a second index step; stateless search reflects it directly.",
            stateful_tool_calls=[
                {"tool_name": "file.write", "args": {"file_id": "f1", "content": "old alpha"}},
                {"tool_name": "search.index", "args": {"file_id": "f1"}},
                {"tool_name": "file.write", "args": {"file_id": "f1", "content": "new beta"}},
                {"tool_name": "search.index", "args": {"file_id": "f1"}},
                {"tool_name": "search.query", "args": {"query": "beta"}},
            ],
            stateless_tool_calls=[
                {"tool_name": "file.write", "args": {"file_id": "f1", "content": "old alpha"}},
                {"tool_name": "file.write", "args": {"file_id": "f1", "content": "new beta"}},
                {"tool_name": "search.query", "args": {"query": "beta"}},
            ],
            goals_stateful=[
                {"type": "indexed_contains", "file_id": "f1", "substring": "beta"},
                {"type": "query_hits_file", "query": "beta", "file_id": "f1"},
            ],
            goals_stateless=[
                {"type": "query_hits_file", "query": "beta", "file_id": "f1"},
            ],
        ),
        ComparisonCase(
            case_name="calendar_conflict_requires_reschedule",
            description="Stateful calendar creation rejects participant conflicts and requires rescheduling; stateless accepts the conflict directly.",
            stateful_tool_calls=[
                {
                    "tool_name": "calendar.create_event",
                    "args": {"event_id": "e1", "title": "Design review", "start_time": 10.0, "end_time": 11.0, "participants": ["alice"]},
                },
                {
                    "tool_name": "calendar.create_event",
                    "args": {"event_id": "e2", "title": "Planning", "start_time": 10.5, "end_time": 11.5, "participants": ["alice"]},
                },
                {
                    "tool_name": "calendar.create_event",
                    "args": {"event_id": "e2", "title": "Planning", "start_time": 11.0, "end_time": 12.0, "participants": ["alice"]},
                },
            ],
            stateless_tool_calls=[
                {
                    "tool_name": "calendar.create_event",
                    "args": {"event_id": "e1", "title": "Design review", "start_time": 10.0, "end_time": 11.0, "participants": ["alice"]},
                },
                {
                    "tool_name": "calendar.create_event",
                    "args": {"event_id": "e2", "title": "Planning", "start_time": 10.5, "end_time": 11.5, "participants": ["alice"]},
                },
            ],
            goals_stateful=[
                {"type": "event_exists", "event_id": "e2"},
                {"type": "event_field_equals", "event_id": "e2", "field": "start_time", "expected": 11.0},
            ],
            goals_stateless=[
                {"type": "event_exists", "event_id": "e2"},
                {"type": "event_field_equals", "event_id": "e2", "field": "start_time", "expected": 10.5},
            ],
        ),
        ComparisonCase(
            case_name="calendar_update_conflict_requires_recovery",
            description="Stateful calendar update rejects moving an event into a conflict; stateless updates directly.",
            stateful_tool_calls=[
                {
                    "tool_name": "calendar.create_event",
                    "args": {"event_id": "e1", "title": "Standup", "start_time": 9.0, "end_time": 10.0, "participants": ["alice"]},
                },
                {
                    "tool_name": "calendar.create_event",
                    "args": {"event_id": "e2", "title": "Sync", "start_time": 10.0, "end_time": 11.0, "participants": ["alice"]},
                },
                {"tool_name": "calendar.update_event", "args": {"event_id": "e2", "start_time": 9.5, "end_time": 10.5}},
                {"tool_name": "calendar.update_event", "args": {"event_id": "e2", "start_time": 11.0, "end_time": 12.0}},
            ],
            stateless_tool_calls=[
                {
                    "tool_name": "calendar.create_event",
                    "args": {"event_id": "e1", "title": "Standup", "start_time": 9.0, "end_time": 10.0, "participants": ["alice"]},
                },
                {
                    "tool_name": "calendar.create_event",
                    "args": {"event_id": "e2", "title": "Sync", "start_time": 10.0, "end_time": 11.0, "participants": ["alice"]},
                },
                {"tool_name": "calendar.update_event", "args": {"event_id": "e2", "start_time": 9.5, "end_time": 10.5}},
            ],
            goals_stateful=[
                {"type": "event_exists", "event_id": "e2"},
                {"type": "event_field_equals", "event_id": "e2", "field": "start_time", "expected": 11.0},
            ],
            goals_stateless=[
                {"type": "event_exists", "event_id": "e2"},
                {"type": "event_field_equals", "event_id": "e2", "field": "start_time", "expected": 9.5},
            ],
        ),
        ComparisonCase(
            case_name="issue_reopen_requires_closed_state",
            description="Stateful issue reopening requires a closed issue and exposes recovery; stateless reopens directly.",
            stateful_tool_calls=[
                {"tool_name": "issue.create", "args": {"issue_id": "iss2", "title": "Regression", "reporter": "alice"}},
                {"tool_name": "issue.reopen", "args": {"issue_id": "iss2", "reason": "still failing"}},
                {"tool_name": "issue.assign", "args": {"issue_id": "iss2", "assignee": "bob"}},
                {"tool_name": "issue.close", "args": {"issue_id": "iss2", "resolution": "fixed"}},
                {"tool_name": "issue.reopen", "args": {"issue_id": "iss2", "reason": "still failing"}},
            ],
            stateless_tool_calls=[
                {"tool_name": "issue.create", "args": {"issue_id": "iss2", "title": "Regression", "reporter": "alice"}},
                {"tool_name": "issue.reopen", "args": {"issue_id": "iss2", "reason": "still failing"}},
            ],
            goals_stateful=[
                {"type": "issue_exists", "issue_id": "iss2"},
                {"type": "issue_status_is", "issue_id": "iss2", "status": "open"},
                {"type": "issue_has_assignee", "issue_id": "iss2", "assignee": "bob"},
            ],
            goals_stateless=[
                {"type": "issue_exists", "issue_id": "iss2"},
                {"type": "issue_status_is", "issue_id": "iss2", "status": "open"},
            ],
        ),
    ]


def build_toolsandbox_stateless_vs_stateful_cases(
    cases: list[ToolSandboxConvertedCase],
) -> list[ComparisonCase]:
    """Build stateless/stateful comparison cases from ToolSandbox converted cases.

    Stateful keeps the full oracle trajectory and all ToolSandbox milestone
    goals. Stateless uses a compact final-state trajectory and drops goals that
    assert helper/search trace calls, matching a final-state-only baseline.
    """
    comparison_cases: list[ComparisonCase] = []
    for case in cases:
        stateless_tool_calls = _compact_toolsandbox_stateless_calls(case)
        stateless_goals = _filter_toolsandbox_stateless_goals(case.goals)
        if not stateless_tool_calls and not stateless_goals:
            continue
        comparison_cases.append(ComparisonCase(
            case_name=f"toolsandbox::{case.scenario_name}",
            description=(
                f"ToolSandbox {case.domain} case. Stateful follows the full oracle trajectory; "
                "stateless evaluates a compact final-state trajectory."
            ),
            stateful_tool_calls=case.oracle_tool_calls,
            stateless_tool_calls=stateless_tool_calls,
            goals_stateful=case.goals,
            goals_stateless=stateless_goals,
            initial_state_stateful=case.initial_state,
            initial_state_stateless=case.initial_state,
        ))
    return comparison_cases


def select_toolsandbox_comparison_subset_cases(
    cases: list[ToolSandboxConvertedCase],
    *,
    group_by: str = "domain",
    per_group: int = 8,
) -> list[ToolSandboxConvertedCase]:
    """Select ToolSandbox cases suitable for stateless/stateful comparison.

    The selected cases must contain at least one final-state goal after dropping
    helper-tool trace assertions. This avoids external-search cases whose only
    milestone is "called helper tool X", which are useful for ToolSandbox oracle
    validation but not for a final-state stateless baseline.
    """
    if not 5 <= per_group <= 10:
        raise ValueError("per_group must be between 5 and 10")
    if group_by not in {"domain", "category"}:
        raise ValueError("group_by must be either 'domain' or 'category'")

    grouped: dict[str, list[ToolSandboxConvertedCase]] = {}
    for case in cases:
        if not _filter_toolsandbox_stateless_goals(case.goals):
            continue
        if not _compact_toolsandbox_stateless_calls(case):
            continue
        group_names = [case.domain or "unknown"] if group_by == "domain" else case.categories or ["uncategorized"]
        for group_name in group_names:
            grouped.setdefault(group_name, []).append(case)

    selected: list[ToolSandboxConvertedCase] = []
    seen: set[str] = set()
    for group_name in sorted(grouped):
        for case in _diverse_toolsandbox_cases(grouped[group_name], per_group):
            if case.scenario_name in seen:
                continue
            selected.append(case)
            seen.add(case.scenario_name)
    return selected


def _clone_state(state: WorldState) -> WorldState:
    return WorldState.from_dict(state.to_dict())


def _compact_toolsandbox_stateless_calls(case: ToolSandboxConvertedCase) -> list[dict[str, Any]]:
    stateful_calls_by_name: dict[str, list[dict[str, Any]]] = {}
    for call in case.oracle_tool_calls:
        stateful_calls_by_name.setdefault(call.get("tool_name", ""), []).append(call)

    calls: list[dict[str, Any]] = []
    for goal in _filter_toolsandbox_stateless_goals(case.goals):
        call = _toolsandbox_goal_to_stateless_call(goal, stateful_calls_by_name, case.initial_state)
        if call is not None:
            calls.append(call)
    return _dedupe_calls(calls)


def _filter_toolsandbox_stateless_goals(goals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    filtered: list[dict[str, Any]] = []
    for goal in goals:
        if goal.get("type") != "toolsandbox_record_exists":
            filtered.append(goal)
            continue
        fields = goal.get("fields", {})
        if goal.get("entity_type") == "sandbox" and "openai_function_name" in fields:
            continue
        filtered.append(goal)
    return filtered


def _toolsandbox_goal_to_stateless_call(
    goal: dict[str, Any],
    stateful_calls_by_name: dict[str, list[dict[str, Any]]],
    initial_state: WorldState,
) -> dict[str, Any] | None:
    goal_type = goal.get("type")
    entity_type = goal.get("entity_type")
    fields = dict(goal.get("fields", {}))

    if goal_type == "toolsandbox_setting_equals":
        return _setting_goal_to_call(goal)

    if entity_type == "contact":
        if goal_type == "toolsandbox_record_absent":
            if not _state_has_matching_record(initial_state, "contact", fields):
                return None
            return {"tool_name": "remove_contact", "args": fields}
        return {"tool_name": _matching_tool_name(stateful_calls_by_name, ["modify_contact", "add_contact"]), "args": fields}

    if entity_type == "reminder":
        if goal_type == "toolsandbox_record_absent":
            if not _state_has_matching_record(initial_state, "reminder", fields):
                return None
            return {"tool_name": "remove_reminder", "args": fields}
        return {"tool_name": _matching_tool_name(stateful_calls_by_name, ["modify_reminder", "add_reminder"]), "args": fields}

    if entity_type == "messaging" and goal_type == "toolsandbox_record_exists":
        return {"tool_name": "send_message_with_phone_number", "args": fields}

    if entity_type == "sandbox" and goal_type == "toolsandbox_record_exists":
        content = fields.get("content")
        if content:
            return {"tool_name": "end_conversation", "args": {"content": content, "recipient": fields.get("recipient", "USER")}}

    return None


def _state_has_matching_record(state: WorldState, entity_type: str, fields: dict[str, Any]) -> bool:
    for entity in state.entities.get(entity_type, {}).values():
        if all(entity.get(field) == expected for field, expected in fields.items()):
            return True
    return False


def _setting_goal_to_call(goal: dict[str, Any]) -> dict[str, Any] | None:
    mapping = {
        "wifi": "set_wifi_status",
        "cellular": "set_cellular_service_status",
        "location_service": "set_location_service_status",
        "low_battery_mode": "set_low_battery_mode_status",
    }
    field = goal.get("field")
    tool_name = mapping.get(field)
    if tool_name is None:
        return None
    return {"tool_name": tool_name, "args": {field: goal.get("expected")}}


def _matching_tool_name(stateful_calls_by_name: dict[str, list[dict[str, Any]]], candidates: list[str]) -> str:
    for candidate in candidates:
        if candidate in stateful_calls_by_name:
            return candidate
    return candidates[-1]


def _dedupe_calls(calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for call in calls:
        key = repr((call.get("tool_name"), sorted((call.get("args") or {}).items())))
        if key in seen:
            continue
        seen.add(key)
        result.append(call)
    return result


def _diverse_toolsandbox_cases(
    cases: list[ToolSandboxConvertedCase],
    limit: int,
) -> list[ToolSandboxConvertedCase]:
    ordered = sorted(cases, key=lambda case: (
        str(case.metadata.get("canonical_task_key") or ""),
        case.scenario_name,
    ))
    selected: list[ToolSandboxConvertedCase] = []
    seen_keys: set[str] = set()
    for case in ordered:
        key = str(case.metadata.get("canonical_task_key") or case.scenario_name)
        if key in seen_keys:
            continue
        selected.append(case)
        seen_keys.add(key)
        if len(selected) >= limit:
            return selected

    selected_names = {case.scenario_name for case in selected}
    for case in ordered:
        if case.scenario_name in selected_names:
            continue
        selected.append(case)
        if len(selected) >= limit:
            break
    return selected
