"""Synthetic cross-tool dependency difficulty-curve experiments."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from toolsim.adapters.toolsandbox_adapter import ToolSandboxConvertedCase
from toolsim.core.world_state import WorldState
from toolsim.evaluators.trajectory_evaluator import TrajectoryLevelEvaluator
from toolsim.runners.comparison_runner import (
    _compact_toolsandbox_stateless_calls,
    _filter_toolsandbox_stateless_goals,
)
from toolsim.runners.experiment_runner import ExperimentResult, ExperimentRunner

DifficultyLevel = str
StrategyName = str

L1_SINGLE_TOOL = "L1_SINGLE_TOOL"
L2_EXPLICIT_DEP = "L2_EXPLICIT_DEP"
L3_IMPLICIT_SIDE_EFFECT = "L3_IMPLICIT_SIDE_EFFECT"

DEFAULT_STRATEGIES = ["direct", "cot", "react", "self_refine"]

_TERMINAL_TOOLS = {"end_conversation"}
_TOOLSANDBOX_HELPER_PREFIXES = ("search_", "get_", "timestamp", "datetime", "convert_", "unit_")
_TOOLSANDBOX_HELPER_NAMES = {
    "calculate_lat_lon_distance",
    "seconds_to_hours_minutes_seconds",
    "search_location_around_lat_lon",
    "search_weather_around_lat_lon",
    "search_holiday",
    "search_stock",
    "search_lat_lon",
}


@dataclass
class DependencyEdge:
    before: str
    after: str
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"before": self.before, "after": self.after, "description": self.description}


@dataclass
class DependencyCurveCase:
    case_name: str
    difficulty_level: DifficultyLevel
    dependency_type: str
    description: str
    goals: list[dict[str, Any]]
    oracle_tool_calls: list[dict[str, Any]]
    strategy_tool_calls: dict[StrategyName, list[dict[str, Any]]]
    initial_state: WorldState = field(default_factory=WorldState)
    required_edges: list[DependencyEdge] = field(default_factory=list)

    def tool_calls_for_strategy(self, strategy: StrategyName) -> list[dict[str, Any]]:
        return self.strategy_tool_calls.get(strategy, self.oracle_tool_calls)

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_name": self.case_name,
            "difficulty_level": self.difficulty_level,
            "dependency_type": self.dependency_type,
            "description": self.description,
            "goals": self.goals,
            "oracle_tool_calls": self.oracle_tool_calls,
            "strategy_tool_calls": self.strategy_tool_calls,
            "initial_state": self.initial_state.to_dict(),
            "required_edges": [edge.to_dict() for edge in self.required_edges],
        }


@dataclass
class DependencyCaseRunResult:
    case_name: str
    difficulty_level: DifficultyLevel
    dependency_type: str
    strategy: StrategyName
    result: ExperimentResult
    final_state_correct: bool
    dependency_completion_rate: float
    wrong_order_call_count: int
    missing_prerequisite_count: int
    side_effect_dependency_success: bool | None
    dependency_repair: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_name": self.case_name,
            "difficulty_level": self.difficulty_level,
            "dependency_type": self.dependency_type,
            "strategy": self.strategy,
            "final_state_correct": self.final_state_correct,
            "dependency_completion_rate": self.dependency_completion_rate,
            "wrong_order_call_count": self.wrong_order_call_count,
            "missing_prerequisite_count": self.missing_prerequisite_count,
            "side_effect_dependency_success": self.side_effect_dependency_success,
            "dependency_repair": self.dependency_repair,
            "result": self.result.to_dict(),
        }


@dataclass
class DependencyGroupMetrics:
    strategy: StrategyName
    difficulty_level: DifficultyLevel
    total_cases: int
    success_count: int
    final_state_correctness: float
    success_rate: float
    invalid_call_rate: float
    recovery_rate: float
    average_trajectory_length: float
    dependency_completion_rate: float
    wrong_order_rate: float
    missing_prerequisite_rate: float
    side_effect_awareness_rate: float | None
    dependency_repair_rate: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy": self.strategy,
            "difficulty_level": self.difficulty_level,
            "total_cases": self.total_cases,
            "success_count": self.success_count,
            "final_state_correctness": self.final_state_correctness,
            "success_rate": self.success_rate,
            "invalid_call_rate": self.invalid_call_rate,
            "recovery_rate": self.recovery_rate,
            "average_trajectory_length": self.average_trajectory_length,
            "dependency_completion_rate": self.dependency_completion_rate,
            "wrong_order_rate": self.wrong_order_rate,
            "missing_prerequisite_rate": self.missing_prerequisite_rate,
            "side_effect_awareness_rate": self.side_effect_awareness_rate,
            "dependency_repair_rate": self.dependency_repair_rate,
        }


@dataclass
class DependencyStrategySummary:
    strategy: StrategyName
    l1_success_rate: float
    l2_success_rate: float
    l3_success_rate: float
    degradation_l1_to_l3: float
    auc_success: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy": self.strategy,
            "l1_success_rate": self.l1_success_rate,
            "l2_success_rate": self.l2_success_rate,
            "l3_success_rate": self.l3_success_rate,
            "degradation_l1_to_l3": self.degradation_l1_to_l3,
            "auc_success": self.auc_success,
        }


@dataclass
class DependencyCurveResult:
    results: list[DependencyCaseRunResult]
    group_metrics: list[DependencyGroupMetrics]
    strategy_summaries: list[DependencyStrategySummary]

    def to_dict(self) -> dict[str, Any]:
        return {
            "results": [result.to_dict() for result in self.results],
            "group_metrics": [metric.to_dict() for metric in self.group_metrics],
            "strategy_summaries": [summary.to_dict() for summary in self.strategy_summaries],
        }


class DependencyCurveRunner:
    """Run synthetic dependency cases across deterministic strategy templates."""

    def __init__(self, experiment_runner: ExperimentRunner | None = None) -> None:
        self._experiment_runner = experiment_runner or ExperimentRunner()

    def run(
        self,
        cases: list[DependencyCurveCase],
        strategies: list[StrategyName] | None = None,
    ) -> DependencyCurveResult:
        selected_strategies = strategies or DEFAULT_STRATEGIES
        results: list[DependencyCaseRunResult] = []
        for case in cases:
            for strategy in selected_strategies:
                results.append(self.run_case(case, strategy))
        group_metrics = _compute_group_metrics(results, selected_strategies)
        return DependencyCurveResult(
            results=results,
            group_metrics=group_metrics,
            strategy_summaries=_compute_strategy_summaries(group_metrics, selected_strategies),
        )

    def run_case(self, case: DependencyCurveCase, strategy: StrategyName) -> DependencyCaseRunResult:
        result = self._experiment_runner.run(
            tool_calls=case.tool_calls_for_strategy(strategy),
            initial_state=WorldState.from_dict(case.initial_state.to_dict()),
            goals=case.goals,
        )
        final_state_correct = result.state_metrics.all_passed if result.state_metrics is not None else False
        dependency_metrics = evaluate_dependency_trace(
            [record.tool_name for record in result.trace],
            case.required_edges,
        )
        trajectory = TrajectoryLevelEvaluator().evaluate(result.trace)
        dependency_repair = bool(final_state_correct and trajectory.failed_steps > 0)
        side_effect_success = None
        if case.difficulty_level == L3_IMPLICIT_SIDE_EFFECT:
            side_effect_success = final_state_correct and dependency_metrics["dependency_completion_rate"] == 1.0

        return DependencyCaseRunResult(
            case_name=case.case_name,
            difficulty_level=case.difficulty_level,
            dependency_type=case.dependency_type,
            strategy=strategy,
            result=result,
            final_state_correct=final_state_correct,
            dependency_completion_rate=dependency_metrics["dependency_completion_rate"],
            wrong_order_call_count=dependency_metrics["wrong_order_call_count"],
            missing_prerequisite_count=dependency_metrics["missing_prerequisite_count"],
            side_effect_dependency_success=side_effect_success,
            dependency_repair=dependency_repair,
        )


def evaluate_dependency_trace(tool_sequence: list[str], edges: list[DependencyEdge]) -> dict[str, Any]:
    completed = 0
    wrong_order = 0
    missing_prereq = 0

    for edge in edges:
        if edge.before == edge.after:
            if sum(1 for tool_name in tool_sequence if tool_name == edge.before) >= 2:
                completed += 1
            else:
                missing_prereq += 1
            continue

        before_indices = _indices(tool_sequence, edge.before)
        after_indices = _indices(tool_sequence, edge.after)
        if not after_indices:
            missing_prereq += 1
            continue
        if not before_indices:
            missing_prereq += 1
            continue
        if any(before_idx < after_idx for before_idx in before_indices for after_idx in after_indices):
            completed += 1
        else:
            wrong_order += 1
            missing_prereq += 1

    return {
        "dependency_completion_rate": completed / len(edges) if edges else 1.0,
        "wrong_order_call_count": wrong_order,
        "missing_prerequisite_count": missing_prereq,
    }


def build_synthetic_dependency_curve_cases() -> list[DependencyCurveCase]:
    """Build synthetic L1/L2/L3 cases for a first difficulty-curve run."""
    return [
        *_build_l1_cases(),
        *_build_l2_cases(),
        *_build_l3_cases(),
    ]


def build_toolsandbox_dependency_curve_cases(
    cases: list[ToolSandboxConvertedCase],
) -> list[DependencyCurveCase]:
    """Convert ToolSandbox cases into dependency-curve cases."""
    curve_cases: list[DependencyCurveCase] = []
    for case in cases:
        difficulty_level = classify_toolsandbox_dependency_level(case)
        if difficulty_level is None:
            continue
        direct_calls = _compact_toolsandbox_stateless_calls(case)
        if not direct_calls:
            continue
        goals = case.goals
        curve_cases.append(DependencyCurveCase(
            case_name=f"toolsandbox::{case.scenario_name}",
            difficulty_level=difficulty_level,
            dependency_type=_dependency_type_for_level(difficulty_level),
            description=f"ToolSandbox {case.domain} dependency case converted from {case.scenario_name}.",
            goals=goals,
            oracle_tool_calls=case.oracle_tool_calls,
            strategy_tool_calls={
                "direct": direct_calls,
                "cot": _toolsandbox_cot_calls(case, difficulty_level, direct_calls),
                "react": _toolsandbox_react_calls(case, difficulty_level, direct_calls),
                "self_refine": case.oracle_tool_calls,
            },
            initial_state=case.initial_state,
            required_edges=_toolsandbox_dependency_edges(case.oracle_tool_calls),
        ))
    return curve_cases


def select_toolsandbox_dependency_subset_cases(
    cases: list[ToolSandboxConvertedCase],
    *,
    per_level: int = 8,
) -> list[ToolSandboxConvertedCase]:
    """Select a balanced ToolSandbox subset for L1/L2/L3 dependency curves."""
    if not 5 <= per_level <= 10:
        raise ValueError("per_level must be between 5 and 10")

    grouped: dict[str, list[ToolSandboxConvertedCase]] = {
        L1_SINGLE_TOOL: [],
        L2_EXPLICIT_DEP: [],
        L3_IMPLICIT_SIDE_EFFECT: [],
    }
    for case in cases:
        if not case.goals:
            continue
        if not _filter_toolsandbox_stateless_goals(case.goals):
            continue
        if not _compact_toolsandbox_stateless_calls(case):
            continue
        level = classify_toolsandbox_dependency_level(case)
        if level is not None:
            grouped[level].append(case)

    selected: list[ToolSandboxConvertedCase] = []
    seen: set[str] = set()
    for level in [L1_SINGLE_TOOL, L2_EXPLICIT_DEP, L3_IMPLICIT_SIDE_EFFECT]:
        for case in _diverse_toolsandbox_dependency_cases(grouped[level], per_level):
            if case.scenario_name in seen:
                continue
            selected.append(case)
            seen.add(case.scenario_name)
    return selected


def classify_toolsandbox_dependency_level(case: ToolSandboxConvertedCase) -> DifficultyLevel | None:
    """Classify a ToolSandbox case into L1/L2/L3 using trace/category rules."""
    tool_names = [call.get("tool_name", "") for call in case.oracle_tool_calls]
    non_terminal = [tool_name for tool_name in tool_names if tool_name not in _TERMINAL_TOOLS]
    helper_count = sum(1 for tool_name in non_terminal if _is_toolsandbox_helper_tool(tool_name))
    final_action_count = sum(1 for tool_name in non_terminal if not _is_toolsandbox_helper_tool(tool_name))

    if not non_terminal:
        return None

    if (
        "STATE_DEPENDENCY" in case.categories
        or "MULTIPLE_USER_TURN" in case.categories and helper_count > 0
        or helper_count >= 2
    ):
        return L3_IMPLICIT_SIDE_EFFECT

    if helper_count > 0 and final_action_count > 0:
        return L2_EXPLICIT_DEP

    if final_action_count == 1 and helper_count == 0 and not _has_absent_goal(case):
        return L1_SINGLE_TOOL

    return None


def _build_l1_cases() -> list[DependencyCurveCase]:
    return [
        _case(
            "l1_file_write",
            L1_SINGLE_TOOL,
            "none",
            "Write a standalone file.",
            [{"tool_name": "file.write", "args": {"file_id": "l1_file", "content": "ready"}}],
            [{"type": "entity_field_equals", "entity_type": "file", "entity_id": "l1_file", "field": "content", "expected": "ready"}],
        ),
        _case(
            "l1_issue_create",
            L1_SINGLE_TOOL,
            "none",
            "Create a standalone issue.",
            [{"tool_name": "issue.create", "args": {"issue_id": "l1_issue", "title": "Standalone"}}],
            [{"type": "issue_status_is", "issue_id": "l1_issue", "status": "open"}],
        ),
        _case(
            "l1_calendar_create",
            L1_SINGLE_TOOL,
            "none",
            "Create a standalone calendar event.",
            [{"tool_name": "calendar.create_event", "args": {"event_id": "l1_event", "title": "Focus", "start_time": 15.0, "end_time": 16.0, "participants": ["ana"]}}],
            [{"type": "event_exists", "event_id": "l1_event"}],
        ),
        _case(
            "l1_wifi_setting",
            L1_SINGLE_TOOL,
            "none",
            "Set Wi-Fi status directly.",
            [{"tool_name": "set_wifi_status", "args": {"wifi": True}}],
            [{"type": "toolsandbox_setting_equals", "field": "wifi", "expected": True}],
        ),
        _case(
            "l1_send_message",
            L1_SINGLE_TOOL,
            "none",
            "Send a direct message.",
            [{"tool_name": "send_message_with_phone_number", "args": {"recipient_phone_number": "+100", "content": "hello"}}],
            [{"type": "toolsandbox_record_exists", "entity_type": "messaging", "fields": {"recipient_phone_number": "+100", "content": "hello"}}],
        ),
    ]


def _build_l2_cases() -> list[DependencyCurveCase]:
    cases: list[DependencyCurveCase] = []

    cases.append(_case(
        "l2_write_index_query",
        L2_EXPLICIT_DEP,
        "explicit",
        "Search depends on explicit indexing.",
        [
            {"tool_name": "file.write", "args": {"file_id": "l2_file", "content": "alpha dependency"}},
            {"tool_name": "search.index", "args": {"file_id": "l2_file"}},
            {"tool_name": "search.query", "args": {"query": "alpha"}},
        ],
        [{"type": "query_hits_file", "query": "alpha", "file_id": "l2_file"}],
        edges=[DependencyEdge("file.write", "search.index"), DependencyEdge("search.index", "search.query")],
        direct=[
            {"tool_name": "file.write", "args": {"file_id": "l2_file", "content": "alpha dependency"}},
            {"tool_name": "search.query", "args": {"query": "alpha"}},
        ],
        cot=[
            {"tool_name": "file.write", "args": {"file_id": "l2_file", "content": "alpha dependency"}},
            {"tool_name": "search.index", "args": {"file_id": "l2_file"}},
            {"tool_name": "search.query", "args": {"query": "alpha"}},
        ],
    ))
    cases.append(_case(
        "l2_issue_assign_close",
        L2_EXPLICIT_DEP,
        "explicit",
        "Closing depends on prior assignment.",
        [
            {"tool_name": "issue.create", "args": {"issue_id": "l2_issue", "title": "Bug"}},
            {"tool_name": "issue.assign", "args": {"issue_id": "l2_issue", "assignee": "bob"}},
            {"tool_name": "issue.close", "args": {"issue_id": "l2_issue", "resolution": "fixed"}},
        ],
        [{"type": "issue_status_is", "issue_id": "l2_issue", "status": "closed"}],
        edges=[DependencyEdge("issue.assign", "issue.close")],
        direct=[
            {"tool_name": "issue.create", "args": {"issue_id": "l2_issue", "title": "Bug"}},
            {"tool_name": "issue.close", "args": {"issue_id": "l2_issue", "resolution": "fixed"}},
        ],
    ))
    cases.append(_case(
        "l2_calendar_search_update",
        L2_EXPLICIT_DEP,
        "explicit",
        "Calendar update depends on finding the event first.",
        [
            {"tool_name": "calendar.create_event", "args": {"event_id": "l2_event", "title": "Sync", "start_time": 9.0, "end_time": 10.0, "participants": ["ana"]}},
            {"tool_name": "calendar.search_events", "args": {"participant": "ana"}},
            {"tool_name": "calendar.update_event", "args": {"event_id": "l2_event", "location": "Room B"}},
        ],
        [{"type": "event_field_equals", "event_id": "l2_event", "field": "location", "expected": "Room B"}],
        edges=[DependencyEdge("calendar.search_events", "calendar.update_event")],
        direct=[
            {"tool_name": "calendar.create_event", "args": {"event_id": "l2_event", "title": "Sync", "start_time": 9.0, "end_time": 10.0, "participants": ["ana"]}},
            {"tool_name": "calendar.update_event", "args": {"event_id": "l2_event", "location": "Room B"}},
        ],
    ))
    cases.append(_case(
        "l2_contact_search_modify",
        L2_EXPLICIT_DEP,
        "explicit",
        "Contact modification depends on searching for the contact.",
        [
            {"tool_name": "search_contacts", "args": {"name": "Ada"}},
            {"tool_name": "modify_contact", "args": {"name": "Ada", "phone_number": "+200"}},
        ],
        [
            {"type": "toolsandbox_record_exists", "entity_type": "sandbox", "fields": {"openai_function_name": "search_contacts"}},
            {"type": "toolsandbox_record_exists", "entity_type": "contact", "fields": {"name": "Ada", "phone_number": "+200"}},
        ],
        initial_state=_state_with_contact("Ada"),
        edges=[DependencyEdge("search_contacts", "modify_contact")],
        direct=[{"tool_name": "modify_contact", "args": {"name": "Ada", "phone_number": "+200"}}],
        cot=[{"tool_name": "modify_contact", "args": {"name": "Ada", "phone_number": "+200"}}],
    ))
    cases.append(_case(
        "l2_timestamp_add_reminder",
        L2_EXPLICIT_DEP,
        "explicit",
        "Reminder creation depends on timestamp conversion.",
        [
            {"tool_name": "datetime_info_to_timestamp", "args": {}},
            {"tool_name": "add_reminder", "args": {"content": "submit form", "reminder_timestamp": 1711098000.0}},
        ],
        [
            {"type": "toolsandbox_record_exists", "entity_type": "sandbox", "fields": {"openai_function_name": "datetime_info_to_timestamp"}},
            {"type": "toolsandbox_record_exists", "entity_type": "reminder", "fields": {"content": "submit form", "reminder_timestamp": 1711098000.0}},
        ],
        edges=[DependencyEdge("datetime_info_to_timestamp", "add_reminder")],
        direct=[{"tool_name": "add_reminder", "args": {"content": "submit form", "reminder_timestamp": 1711098000.0}}],
        cot=[{"tool_name": "add_reminder", "args": {"content": "submit form", "reminder_timestamp": 1711098000.0}}],
    ))
    return cases


def _build_l3_cases() -> list[DependencyCurveCase]:
    return [
        _case(
            "l3_delayed_reindex",
            L3_IMPLICIT_SIDE_EFFECT,
            "implicit_side_effect",
            "Search depends on a delayed reindex side effect.",
            [
                {"tool_name": "file.write", "args": {"file_id": "l3_delay", "content": "delta payload", "schedule_search_reindex": True, "reindex_delay": 2.0}},
                {"tool_name": "search.query", "args": {"query": "delta"}, "advance_time": 2.0},
            ],
            [{"type": "query_hits_file", "query": "delta", "file_id": "l3_delay"}],
            edges=[DependencyEdge("file.write", "search.query")],
            direct=[
                {"tool_name": "file.write", "args": {"file_id": "l3_delay", "content": "delta payload", "schedule_search_reindex": True, "reindex_delay": 2.0}},
                {"tool_name": "search.query", "args": {"query": "delta"}},
            ],
            cot=[
                {"tool_name": "file.write", "args": {"file_id": "l3_delay", "content": "delta payload", "schedule_search_reindex": True, "reindex_delay": 2.0}},
                {"tool_name": "search.query", "args": {"query": "delta"}},
            ],
        ),
        _case(
            "l3_reindex_after_overwrite",
            L3_IMPLICIT_SIDE_EFFECT,
            "implicit_side_effect",
            "Fresh retrieval depends on re-indexing after overwrite.",
            [
                {"tool_name": "file.write", "args": {"file_id": "l3_snapshot", "content": "old alpha"}},
                {"tool_name": "search.index", "args": {"file_id": "l3_snapshot"}},
                {"tool_name": "file.write", "args": {"file_id": "l3_snapshot", "content": "new beta"}},
                {"tool_name": "search.index", "args": {"file_id": "l3_snapshot"}},
                {"tool_name": "search.query", "args": {"query": "beta"}},
            ],
            [{"type": "query_hits_file", "query": "beta", "file_id": "l3_snapshot"}],
            edges=[DependencyEdge("file.write", "search.index"), DependencyEdge("search.index", "search.query")],
            direct=[
                {"tool_name": "file.write", "args": {"file_id": "l3_snapshot", "content": "old alpha"}},
                {"tool_name": "search.index", "args": {"file_id": "l3_snapshot"}},
                {"tool_name": "file.write", "args": {"file_id": "l3_snapshot", "content": "new beta"}},
                {"tool_name": "search.query", "args": {"query": "beta"}},
            ],
            cot=[
                {"tool_name": "file.write", "args": {"file_id": "l3_snapshot", "content": "old alpha"}},
                {"tool_name": "search.index", "args": {"file_id": "l3_snapshot"}},
                {"tool_name": "file.write", "args": {"file_id": "l3_snapshot", "content": "new beta"}},
                {"tool_name": "search.query", "args": {"query": "beta"}},
            ],
            react=[
                {"tool_name": "file.write", "args": {"file_id": "l3_snapshot", "content": "old alpha"}},
                {"tool_name": "search.index", "args": {"file_id": "l3_snapshot"}},
                {"tool_name": "file.write", "args": {"file_id": "l3_snapshot", "content": "new beta"}},
                {"tool_name": "search.query", "args": {"query": "beta"}},
            ],
        ),
        _case(
            "l3_issue_close_recovery",
            L3_IMPLICIT_SIDE_EFFECT,
            "implicit_side_effect",
            "Issue close failure requires assignment repair and retry.",
            [
                {"tool_name": "issue.create", "args": {"issue_id": "l3_issue", "title": "Crash"}},
                {"tool_name": "issue.close", "args": {"issue_id": "l3_issue", "resolution": "fixed"}},
                {"tool_name": "issue.assign", "args": {"issue_id": "l3_issue", "assignee": "bob"}},
                {"tool_name": "issue.close", "args": {"issue_id": "l3_issue", "resolution": "fixed"}},
            ],
            [
                {"type": "issue_status_is", "issue_id": "l3_issue", "status": "closed"},
                {"type": "issue_has_assignee", "issue_id": "l3_issue", "assignee": "bob"},
            ],
            edges=[DependencyEdge("issue.assign", "issue.close")],
            direct=[
                {"tool_name": "issue.create", "args": {"issue_id": "l3_issue", "title": "Crash"}},
                {"tool_name": "issue.close", "args": {"issue_id": "l3_issue", "resolution": "fixed"}},
            ],
            cot=[
                {"tool_name": "issue.create", "args": {"issue_id": "l3_issue", "title": "Crash"}},
                {"tool_name": "issue.assign", "args": {"issue_id": "l3_issue", "assignee": "bob"}},
                {"tool_name": "issue.close", "args": {"issue_id": "l3_issue", "resolution": "fixed"}},
            ],
            react=[
                {"tool_name": "issue.create", "args": {"issue_id": "l3_issue", "title": "Crash"}},
                {"tool_name": "issue.assign", "args": {"issue_id": "l3_issue", "assignee": "bob"}},
                {"tool_name": "issue.close", "args": {"issue_id": "l3_issue", "resolution": "fixed"}},
            ],
        ),
        _case(
            "l3_calendar_conflict_recovery",
            L3_IMPLICIT_SIDE_EFFECT,
            "implicit_side_effect",
            "Calendar conflict requires non-conflicting retry.",
            [
                {"tool_name": "calendar.create_event", "args": {"event_id": "l3_e1", "title": "Review", "start_time": 10.0, "end_time": 11.0, "participants": ["ana"]}},
                {"tool_name": "calendar.create_event", "args": {"event_id": "l3_e2", "title": "Plan", "start_time": 10.5, "end_time": 11.5, "participants": ["ana"]}},
                {"tool_name": "calendar.create_event", "args": {"event_id": "l3_e2", "title": "Plan", "start_time": 11.0, "end_time": 12.0, "participants": ["ana"]}},
            ],
            [{"type": "event_field_equals", "event_id": "l3_e2", "field": "start_time", "expected": 11.0}],
            edges=[DependencyEdge("calendar.create_event", "calendar.create_event")],
            direct=[
                {"tool_name": "calendar.create_event", "args": {"event_id": "l3_e1", "title": "Review", "start_time": 10.0, "end_time": 11.0, "participants": ["ana"]}},
                {"tool_name": "calendar.create_event", "args": {"event_id": "l3_e2", "title": "Plan", "start_time": 10.5, "end_time": 11.5, "participants": ["ana"]}},
            ],
            cot=[
                {"tool_name": "calendar.create_event", "args": {"event_id": "l3_e1", "title": "Review", "start_time": 10.0, "end_time": 11.0, "participants": ["ana"]}},
                {"tool_name": "calendar.create_event", "args": {"event_id": "l3_e2", "title": "Plan", "start_time": 11.0, "end_time": 12.0, "participants": ["ana"]}},
            ],
            react=[
                {"tool_name": "calendar.create_event", "args": {"event_id": "l3_e1", "title": "Review", "start_time": 10.0, "end_time": 11.0, "participants": ["ana"]}},
                {"tool_name": "calendar.create_event", "args": {"event_id": "l3_e2", "title": "Plan", "start_time": 11.0, "end_time": 12.0, "participants": ["ana"]}},
            ],
        ),
        _case(
            "l3_search_message_contact_update",
            L3_IMPLICIT_SIDE_EFFECT,
            "implicit_side_effect",
            "Message search identifies which contact to update.",
            [
                {"tool_name": "get_current_timestamp", "args": {}},
                {"tool_name": "search_messages", "args": {"content": "invoice"}},
                {"tool_name": "search_contacts", "args": {"name": "Mira"}},
                {"tool_name": "modify_contact", "args": {"name": "Mira", "phone_number": "+333"}},
            ],
            [
                {"type": "toolsandbox_record_exists", "entity_type": "sandbox", "fields": {"openai_function_name": "search_messages"}},
                {"type": "toolsandbox_record_exists", "entity_type": "sandbox", "fields": {"openai_function_name": "search_contacts"}},
                {"type": "toolsandbox_record_exists", "entity_type": "contact", "fields": {"name": "Mira", "phone_number": "+333"}},
            ],
            initial_state=_state_with_contact("Mira"),
            edges=[DependencyEdge("search_messages", "search_contacts"), DependencyEdge("search_contacts", "modify_contact")],
            direct=[{"tool_name": "modify_contact", "args": {"name": "Mira", "phone_number": "+333"}}],
            cot=[
                {"tool_name": "search_contacts", "args": {"name": "Mira"}},
                {"tool_name": "modify_contact", "args": {"name": "Mira", "phone_number": "+333"}},
            ],
            react=[
                {"tool_name": "search_messages", "args": {"content": "invoice"}},
                {"tool_name": "search_contacts", "args": {"name": "Mira"}},
                {"tool_name": "modify_contact", "args": {"name": "Mira", "phone_number": "+333"}},
            ],
        ),
    ]


def _case(
    case_name: str,
    difficulty_level: DifficultyLevel,
    dependency_type: str,
    description: str,
    oracle_tool_calls: list[dict[str, Any]],
    goals: list[dict[str, Any]],
    *,
    initial_state: WorldState | None = None,
    edges: list[DependencyEdge] | None = None,
    direct: list[dict[str, Any]] | None = None,
    cot: list[dict[str, Any]] | None = None,
    react: list[dict[str, Any]] | None = None,
    self_refine: list[dict[str, Any]] | None = None,
) -> DependencyCurveCase:
    return DependencyCurveCase(
        case_name=case_name,
        difficulty_level=difficulty_level,
        dependency_type=dependency_type,
        description=description,
        goals=goals,
        oracle_tool_calls=oracle_tool_calls,
        initial_state=initial_state or WorldState(),
        required_edges=edges or [],
        strategy_tool_calls={
            "direct": direct if direct is not None else oracle_tool_calls,
            "cot": cot if cot is not None else oracle_tool_calls,
            "react": react if react is not None else oracle_tool_calls,
            "self_refine": self_refine if self_refine is not None else oracle_tool_calls,
        },
    )


def _state_with_contact(name: str) -> WorldState:
    state = WorldState()
    state.set_entity("contact", f"contact_{name.lower()}", {
        "person_id": f"contact_{name.lower()}",
        "name": name,
        "phone_number": None,
        "relationship": None,
        "is_self": False,
    })
    return state


def _dependency_type_for_level(level: DifficultyLevel) -> str:
    if level == L1_SINGLE_TOOL:
        return "none"
    if level == L2_EXPLICIT_DEP:
        return "explicit"
    return "implicit_side_effect"


def _has_absent_goal(case: ToolSandboxConvertedCase) -> bool:
    return any(goal.get("type") == "toolsandbox_record_absent" for goal in case.goals)


def _toolsandbox_cot_calls(
    case: ToolSandboxConvertedCase,
    difficulty_level: DifficultyLevel,
    direct_calls: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if difficulty_level in {L1_SINGLE_TOOL, L2_EXPLICIT_DEP}:
        return case.oracle_tool_calls
    return _drop_first_matching_tool(case.oracle_tool_calls, _is_deep_implicit_toolsandbox_helper) or direct_calls


def _toolsandbox_react_calls(
    case: ToolSandboxConvertedCase,
    difficulty_level: DifficultyLevel,
    direct_calls: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if difficulty_level in {L1_SINGLE_TOOL, L2_EXPLICIT_DEP}:
        return case.oracle_tool_calls
    if len(case.oracle_tool_calls) >= 5:
        return _drop_first_matching_tool(case.oracle_tool_calls, _is_deep_implicit_toolsandbox_helper) or case.oracle_tool_calls
    return case.oracle_tool_calls or direct_calls


def _toolsandbox_dependency_edges(tool_calls: list[dict[str, Any]]) -> list[DependencyEdge]:
    tool_names = [call.get("tool_name", "") for call in tool_calls if call.get("tool_name") not in _TERMINAL_TOOLS]
    edges: list[DependencyEdge] = []
    for before, after in zip(tool_names, tool_names[1:]):
        if before == after:
            continue
        if _is_toolsandbox_helper_tool(before) or _is_toolsandbox_helper_tool(after):
            edges.append(DependencyEdge(before=before, after=after, description="ToolSandbox oracle order dependency"))
    return edges


def _is_toolsandbox_helper_tool(tool_name: str) -> bool:
    return tool_name in _TOOLSANDBOX_HELPER_NAMES or tool_name.startswith(_TOOLSANDBOX_HELPER_PREFIXES)


def _is_deep_implicit_toolsandbox_helper(tool_name: str) -> bool:
    if tool_name in {"get_current_timestamp", "search_messages", "search_reminder"}:
        return True
    return tool_name in _TOOLSANDBOX_HELPER_NAMES


def _drop_first_matching_tool(
    tool_calls: list[dict[str, Any]],
    predicate,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    dropped = False
    for call in tool_calls:
        tool_name = call.get("tool_name", "")
        if not dropped and predicate(tool_name):
            dropped = True
            continue
        result.append(call)
    return result


def _diverse_toolsandbox_dependency_cases(
    cases: list[ToolSandboxConvertedCase],
    limit: int,
) -> list[ToolSandboxConvertedCase]:
    ordered = _round_robin_by_domain(sorted(cases, key=lambda case: (
        case.domain,
        str(case.metadata.get("canonical_task_key") or ""),
        case.scenario_name,
    )))
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


def _round_robin_by_domain(cases: list[ToolSandboxConvertedCase]) -> list[ToolSandboxConvertedCase]:
    by_domain: dict[str, list[ToolSandboxConvertedCase]] = {}
    for case in cases:
        by_domain.setdefault(case.domain or "unknown", []).append(case)

    result: list[ToolSandboxConvertedCase] = []
    while any(by_domain.values()):
        for domain in sorted(by_domain):
            if by_domain[domain]:
                result.append(by_domain[domain].pop(0))
    return result


def _compute_group_metrics(
    results: list[DependencyCaseRunResult],
    strategies: list[StrategyName],
) -> list[DependencyGroupMetrics]:
    metrics: list[DependencyGroupMetrics] = []
    for strategy in strategies:
        for level in [L1_SINGLE_TOOL, L2_EXPLICIT_DEP, L3_IMPLICIT_SIDE_EFFECT]:
            group = [result for result in results if result.strategy == strategy and result.difficulty_level == level]
            metrics.append(_summarize_group(strategy, level, group))
    return metrics


def _summarize_group(
    strategy: StrategyName,
    difficulty_level: DifficultyLevel,
    group: list[DependencyCaseRunResult],
) -> DependencyGroupMetrics:
    total_cases = len(group)
    total_calls = sum(item.result.call_metrics.total_calls for item in group)
    successful_calls = sum(item.result.call_metrics.successful_calls for item in group)
    invalid_calls = sum(item.result.call_metrics.invalid_calls for item in group)
    recovery_opportunities = sum(1 for item in group if item.result.call_metrics.failed_calls > 0)
    recovered = sum(1 for item in group if item.result.call_metrics.failed_calls > 0 and item.final_state_correct)
    side_effect_cases = [item for item in group if item.side_effect_dependency_success is not None]

    return DependencyGroupMetrics(
        strategy=strategy,
        difficulty_level=difficulty_level,
        total_cases=total_cases,
        success_count=sum(1 for item in group if item.final_state_correct),
        final_state_correctness=_rate(sum(1 for item in group if item.final_state_correct), total_cases),
        success_rate=_rate(successful_calls, total_calls),
        invalid_call_rate=_rate(invalid_calls, total_calls),
        recovery_rate=_rate(recovered, recovery_opportunities),
        average_trajectory_length=_rate(total_calls, total_cases),
        dependency_completion_rate=_rate(sum(item.dependency_completion_rate for item in group), total_cases),
        wrong_order_rate=_rate(sum(1 for item in group if item.wrong_order_call_count > 0), total_cases),
        missing_prerequisite_rate=_rate(sum(1 for item in group if item.missing_prerequisite_count > 0), total_cases),
        side_effect_awareness_rate=(
            _rate(sum(1 for item in side_effect_cases if item.side_effect_dependency_success), len(side_effect_cases))
            if side_effect_cases
            else None
        ),
        dependency_repair_rate=_rate(sum(1 for item in group if item.dependency_repair), total_cases),
    )


def _compute_strategy_summaries(
    group_metrics: list[DependencyGroupMetrics],
    strategies: list[StrategyName],
) -> list[DependencyStrategySummary]:
    by_key = {(metric.strategy, metric.difficulty_level): metric for metric in group_metrics}
    summaries: list[DependencyStrategySummary] = []
    for strategy in strategies:
        l1 = by_key[(strategy, L1_SINGLE_TOOL)].final_state_correctness
        l2 = by_key[(strategy, L2_EXPLICIT_DEP)].final_state_correctness
        l3 = by_key[(strategy, L3_IMPLICIT_SIDE_EFFECT)].final_state_correctness
        summaries.append(DependencyStrategySummary(
            strategy=strategy,
            l1_success_rate=l1,
            l2_success_rate=l2,
            l3_success_rate=l3,
            degradation_l1_to_l3=l1 - l3,
            auc_success=(l1 + l2 + l3) / 3,
        ))
    return summaries


def _indices(items: list[str], value: str) -> list[int]:
    return [index for index, item in enumerate(items) if item == value]


def _rate(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0
