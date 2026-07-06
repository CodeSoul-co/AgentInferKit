"""Backend migration experiments for mock, sandbox, and live-like execution."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from toolsim.adapters.toolsandbox_adapter import convert_toolsandbox_file
from toolsim.backends.base import BaseBackend
from toolsim.backends.live_like_backend import LiveLikeBackend
from toolsim.backends.mock_backend import MockBackend
from toolsim.backends.sandbox_backend import SandboxBackend
from toolsim.core.world_state import WorldState
from toolsim.execution.stateful_executor import ExecutorConfig
from toolsim.faults import FaultProfile
from toolsim.runners.experiment_runner import ExperimentResult, ExperimentRunner
from toolsim.tools.apibank_runtime import APIBANK_RUNTIME_NAME
from toolsim.tools.toolsandbox_runtime import ensure_toolsandbox_state

BACKENDS = ["mock", "sandbox", "live_like"]
STRATEGIES = ["direct", "cot", "react", "self_refine"]


@dataclass
class BackendMigrationCase:
    case_name: str
    source: str
    description: str
    goals: list[dict[str, Any]]
    target_tool: str
    live_like_fault: str
    live_like_fault_count: int
    strategy_tool_calls: dict[str, list[dict[str, Any]]]
    initial_state: WorldState = field(default_factory=WorldState)

    def tool_calls_for_strategy(self, strategy: str) -> list[dict[str, Any]]:
        return self.strategy_tool_calls.get(strategy, self.strategy_tool_calls["direct"])


@dataclass
class BackendMigrationRunResult:
    case_name: str
    source: str
    strategy: str
    backend: str
    target_tool: str
    live_like_fault: str
    live_like_fault_count: int
    final_state_correct: bool
    all_calls_succeeded: bool
    invalid_call_rate: float
    recovery_detected: bool
    trajectory_length: int
    latency_ms: float
    state_diverged_from_mock: bool
    result: ExperimentResult

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_name": self.case_name,
            "source": self.source,
            "strategy": self.strategy,
            "backend": self.backend,
            "target_tool": self.target_tool,
            "live_like_fault": self.live_like_fault,
            "live_like_fault_count": self.live_like_fault_count,
            "final_state_correct": self.final_state_correct,
            "all_calls_succeeded": self.all_calls_succeeded,
            "invalid_call_rate": self.invalid_call_rate,
            "recovery_detected": self.recovery_detected,
            "trajectory_length": self.trajectory_length,
            "latency_ms": self.latency_ms,
            "state_diverged_from_mock": self.state_diverged_from_mock,
            "result": self.result.to_dict(),
        }


@dataclass
class BackendMigrationGroupMetrics:
    strategy: str
    backend: str
    total_cases: int
    final_state_correctness: float
    migration_gap: float
    state_divergence_rate: float
    invalid_call_rate: float
    recovery_rate: float
    average_trajectory_length: float
    average_latency_ms: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy": self.strategy,
            "backend": self.backend,
            "total_cases": self.total_cases,
            "final_state_correctness": self.final_state_correctness,
            "migration_gap": self.migration_gap,
            "state_divergence_rate": self.state_divergence_rate,
            "invalid_call_rate": self.invalid_call_rate,
            "recovery_rate": self.recovery_rate,
            "average_trajectory_length": self.average_trajectory_length,
            "average_latency_ms": self.average_latency_ms,
        }


@dataclass
class BackendMigrationResult:
    results: list[BackendMigrationRunResult]
    group_metrics: list[BackendMigrationGroupMetrics]

    def to_dict(self) -> dict[str, Any]:
        return {
            "results": [result.to_dict() for result in self.results],
            "group_metrics": [metric.to_dict() for metric in self.group_metrics],
        }


class BackendMigrationRunner:
    """Run backend migration cases across strategies and backend realism levels."""

    def run(
        self,
        cases: list[BackendMigrationCase],
        strategies: list[str] | None = None,
        backends: list[str] | None = None,
    ) -> BackendMigrationResult:
        selected_strategies = strategies or STRATEGIES
        selected_backends = backends or BACKENDS
        results: list[BackendMigrationRunResult] = []

        for case in cases:
            mock_success_by_strategy: dict[str, bool] = {}
            for strategy in selected_strategies:
                mock_result = self.run_case(case, strategy, "mock", state_diverged_from_mock=False)
                mock_success_by_strategy[strategy] = mock_result.final_state_correct
                results.append(mock_result)

                for backend in selected_backends:
                    if backend == "mock":
                        continue
                    backend_result = self.run_case(
                        case,
                        strategy,
                        backend,
                        state_diverged_from_mock=False,
                    )
                    backend_result.state_diverged_from_mock = (
                        backend_result.final_state_correct != mock_success_by_strategy[strategy]
                    )
                    results.append(backend_result)

        return BackendMigrationResult(
            results=results,
            group_metrics=_compute_group_metrics(results, selected_strategies, selected_backends),
        )

    def run_case(
        self,
        case: BackendMigrationCase,
        strategy: str,
        backend_name: str,
        *,
        state_diverged_from_mock: bool,
    ) -> BackendMigrationRunResult:
        backend = _backend_for_name(backend_name, case.case_name)
        runner = ExperimentRunner(
            executor_config=ExecutorConfig(fault_profile=_fault_profile_for_backend(case, backend_name)),
            backend=backend,
        )
        result = runner.run(
            tool_calls=case.tool_calls_for_strategy(strategy),
            initial_state=_clone_state(case.initial_state),
            goals=case.goals,
            backend=backend,
        )
        final_state_correct = result.state_metrics.all_passed if result.state_metrics is not None else False
        recovery_detected = backend_name == "live_like" and result.call_metrics.failed_calls > 0 and final_state_correct
        latency_ms = sum(record.duration_ms for record in result.trace)

        return BackendMigrationRunResult(
            case_name=case.case_name,
            source=case.source,
            strategy=strategy,
            backend=backend_name,
            target_tool=case.target_tool,
            live_like_fault=case.live_like_fault,
            live_like_fault_count=case.live_like_fault_count,
            final_state_correct=final_state_correct,
            all_calls_succeeded=result.all_calls_succeeded,
            invalid_call_rate=result.call_metrics.invalid_calls / result.call_metrics.total_calls if result.call_metrics.total_calls else 0.0,
            recovery_detected=recovery_detected,
            trajectory_length=len(result.trace),
            latency_ms=latency_ms,
            state_diverged_from_mock=state_diverged_from_mock,
            result=result,
        )


def build_backend_migration_cases(
    *,
    include_synthetic: bool = True,
    include_apibank: bool = True,
    include_toolsandbox: bool = True,
    toolsandbox_path: str | Path | None = None,
    toolsandbox_limit: int = 12,
) -> list[BackendMigrationCase]:
    cases: list[BackendMigrationCase] = []
    if include_synthetic:
        cases.extend(_build_synthetic_cases())
        cases.extend(_build_synthetic_semantic_recovery_cases())
    if include_apibank:
        cases.extend(_build_apibank_cases())
    if include_toolsandbox:
        input_path = Path(toolsandbox_path) if toolsandbox_path is not None else _default_toolsandbox_path()
        if input_path.exists():
            cases.extend(_build_toolsandbox_cases(input_path, toolsandbox_limit))
        elif toolsandbox_path is not None:
            raise FileNotFoundError(input_path)
    return cases


def render_backend_migration_markdown(result: BackendMigrationResult) -> str:
    lines = [
        "# Backend Migration Report",
        "",
        "## Backend Migration Metrics",
        "",
        "| Strategy | Backend | Cases | Final Correct | Migration Gap | State Divergence | Invalid Calls | Recovery | Avg Steps | Avg Latency ms |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for metric in result.group_metrics:
        lines.append(
            f"| {metric.strategy} | {metric.backend} | {metric.total_cases} | "
            f"{_pct(metric.final_state_correctness)} | {_pct(metric.migration_gap)} | "
            f"{_pct(metric.state_divergence_rate)} | {_pct(metric.invalid_call_rate)} | "
            f"{_pct(metric.recovery_rate)} | {metric.average_trajectory_length:.2f} | "
            f"{metric.average_latency_ms:.2f} |"
        )
    lines.extend([
        "",
        "## Live-like Fault Breakdown",
        "",
        "| Strategy | Fault Type | Cases | Final Correct | Recovery | Avg Steps | Avg Latency ms |",
        "|---|---|---:|---:|---:|---:|---:|",
    ])
    for strategy in STRATEGIES:
        fault_types = sorted({
            item.live_like_fault
            for item in result.results
            if item.backend == "live_like" and item.strategy == strategy
        })
        for fault_type in fault_types:
            group = [
                item for item in result.results
                if item.backend == "live_like"
                and item.strategy == strategy
                and item.live_like_fault == fault_type
            ]
            total = len(group)
            recovery_opportunities = sum(1 for item in group if item.result.call_metrics.failed_calls > 0)
            lines.append(
                f"| {strategy} | {fault_type} | {total} | "
                f"{_pct(_rate(sum(1 for item in group if item.final_state_correct), total))} | "
                f"{_pct(_rate(sum(1 for item in group if item.recovery_detected), recovery_opportunities))} | "
                f"{_rate(sum(item.trajectory_length for item in group), total):.2f} | "
                f"{_rate(sum(item.latency_ms for item in group), total):.2f} |"
            )

    lines.extend([
        "",
        "## Interpretation",
        _build_interpretation(result),
        "",
    ])
    return "\n".join(lines)


def _build_synthetic_cases() -> list[BackendMigrationCase]:
    contact_state = WorldState()
    contact_state.set_entity("contact", "mig_ada", {
        "person_id": "mig_ada",
        "name": "Ada",
        "phone_number": "+000",
        "relationship": None,
        "is_self": False,
    })
    messaging_state = _toolsandbox_base_state()

    templates = [
        (
            "file_write",
            "file.write",
            "timeout",
            1,
            [{"tool_name": "file.write", "args": {"file_id": "mig_file", "content": "ready"}}],
            [{"type": "entity_field_equals", "entity_type": "file", "entity_id": "mig_file", "field": "content", "expected": "ready"}],
            WorldState(),
        ),
        (
            "wifi_setting",
            "set_wifi_status",
            "schema_drift",
            1,
            [{"tool_name": "set_wifi_status", "args": {"wifi": True}}],
            [{"type": "toolsandbox_setting_equals", "field": "wifi", "expected": True}],
            WorldState(),
        ),
        (
            "contact_modify",
            "modify_contact",
            "persistent_timeout",
            2,
            [{"tool_name": "modify_contact", "args": {"person_id": "mig_ada", "name": "Ada", "phone_number": "+200"}}],
            [{"type": "toolsandbox_record_exists", "entity_type": "contact", "fields": {"name": "Ada", "phone_number": "+200"}}],
            contact_state,
        ),
        (
            "write_index_query",
            "search.index",
            "persistent_timeout",
            2,
            [
                {"tool_name": "file.write", "args": {"file_id": "mig_search", "content": "alpha"}},
                {"tool_name": "search.index", "args": {"file_id": "mig_search"}},
                {"tool_name": "search.query", "args": {"query": "alpha"}},
            ],
            [{"type": "query_hits_file", "query": "alpha", "file_id": "mig_search"}],
            WorldState(),
        ),
        (
            "send_message",
            "send_message_with_phone_number",
            "hard_schema_drift",
            3,
            [{"tool_name": "send_message_with_phone_number", "args": {"recipient_phone_number": "+999", "content": "hello"}}],
            [{"type": "toolsandbox_record_exists", "entity_type": "messaging", "fields": {"recipient_phone_number": "+999", "content": "hello"}}],
            messaging_state,
        ),
    ]

    cases: list[BackendMigrationCase] = []
    for name, target_tool, fault_type, fault_count, direct_calls, goals, state in templates:
        strategy_calls = _strategy_calls_with_retry(direct_calls, target_tool)
        cases.append(BackendMigrationCase(
            case_name=f"synthetic_backend::{name}",
            source="synthetic_backend",
            description=f"Synthetic backend migration case for {name}; live-like fault={fault_type}:{fault_count}.",
            goals=goals,
            target_tool=target_tool,
            live_like_fault=fault_type,
            live_like_fault_count=fault_count,
            strategy_tool_calls=strategy_calls,
            initial_state=state,
        ))
    return cases


def _build_apibank_cases() -> list[BackendMigrationCase]:
    return [
        _apibank_case(
            "forgot_password_timeout",
            "ForgotPassword",
            _apibank_forgot_password_calls("reset-timeout"),
            _forgot_password_goals("reset-timeout"),
            "timeout",
            1,
            "Account recovery workflow: ForgotPassword times out once before code verification succeeds.",
        ),
        _apibank_case(
            "forgot_password_persistent_timeout",
            "ForgotPassword",
            _apibank_forgot_password_calls("reset-persistent"),
            _forgot_password_goals("reset-persistent"),
            "persistent_timeout",
            2,
            "Account recovery workflow: ForgotPassword fails twice, requiring stronger retry policies.",
        ),
        _apibank_case(
            "forgot_password_schema_drift",
            "ForgotPassword",
            _apibank_forgot_password_calls("reset-schema"),
            _forgot_password_goals("reset-schema"),
            "schema_drift",
            1,
            "Account recovery workflow: ForgotPassword sees a recoverable schema-drift failure.",
        ),
        _apibank_case(
            "modify_password_timeout",
            "ModifyPassword",
            _apibank_modify_password_calls("mod-timeout"),
            _account_password_goal("mod-timeout"),
            "timeout",
            1,
            "Authenticated account workflow: GetUserToken then ModifyPassword with one timeout.",
        ),
        _apibank_case(
            "modify_password_persistent_timeout",
            "ModifyPassword",
            _apibank_modify_password_calls("mod-persistent"),
            _account_password_goal("mod-persistent"),
            "persistent_timeout",
            2,
            "Authenticated account workflow: ModifyPassword needs more than one retry to recover.",
        ),
        _apibank_case(
            "check_token_modify_password_schema_drift",
            "ModifyPassword",
            _apibank_check_then_modify_password_calls("mod-schema"),
            _account_password_goal("mod-schema"),
            "schema_drift",
            1,
            "Token-check workflow: CheckToken precedes ModifyPassword under schema drift.",
        ),
        _apibank_case(
            "add_agenda_timeout",
            "AddAgenda",
            _apibank_add_agenda_calls("write paper", "2026-07-01 09:00:00", "Lab A"),
            _agenda_goal("1", "write paper", "2026-07-01 09:00:00", "Lab A"),
            "timeout",
            1,
            "Agenda workflow: AddAgenda times out once before persisting a schedule item.",
        ),
        _apibank_case(
            "add_agenda_schema_drift",
            "AddAgenda",
            _apibank_add_agenda_calls("meet advisor", "2026-07-02 10:00:00", "Office 3"),
            _agenda_goal("1", "meet advisor", "2026-07-02 10:00:00", "Office 3"),
            "schema_drift",
            1,
            "Agenda workflow: AddAgenda recovers from a schema-drift failure.",
        ),
        _apibank_case(
            "add_agenda_persistent_timeout",
            "AddAgenda",
            _apibank_add_agenda_calls("submit abstract", "2026-07-03 11:00:00", "Online"),
            _agenda_goal("1", "submit abstract", "2026-07-03 11:00:00", "Online"),
            "persistent_timeout",
            2,
            "Agenda workflow: AddAgenda fails twice and tests stronger recovery strategies.",
        ),
        _apibank_case(
            "add_modify_agenda_timeout",
            "ModifyAgenda",
            _apibank_add_modify_query_agenda_calls(
                "draft slides",
                "2026-07-04 12:00:00",
                "Room 1",
                "2026-07-04 15:00:00",
                "Room 2",
            ),
            _agenda_goal("1", "draft slides", "2026-07-04 15:00:00", "Room 2"),
            "timeout",
            1,
            "Agenda dependency workflow: AddAgenda succeeds, then ModifyAgenda times out once.",
        ),
        _apibank_case(
            "add_modify_agenda_schema_drift",
            "ModifyAgenda",
            _apibank_add_modify_query_agenda_calls(
                "review notes",
                "2026-07-05 13:00:00",
                "Library",
                "2026-07-05 16:00:00",
                "Library B",
            ),
            _agenda_goal("1", "review notes", "2026-07-05 16:00:00", "Library B"),
            "schema_drift",
            1,
            "Agenda dependency workflow: ModifyAgenda recovers after a schema-drift failure.",
        ),
        _apibank_case(
            "preseeded_modify_agenda_persistent_timeout",
            "ModifyAgenda",
            _apibank_modify_query_agenda_calls(
                "group sync",
                "2026-07-06 14:00:00",
                "2026-07-06 17:00:00",
                "Room C",
            ),
            _agenda_goal("1", "group sync", "2026-07-06 17:00:00", "Room C"),
            "persistent_timeout",
            2,
            "Agenda state update workflow: ModifyAgenda acts on a preseeded database row.",
            initial_state=_apibank_state(
                agenda={
                    "1": {
                        "username": "foo",
                        "content": "group sync",
                        "time": "2026-07-06 14:00:00",
                        "location": "Room A",
                    }
                }
            ),
        ),
        _apibank_case(
            "add_agenda_hard_schema_drift",
            "AddAgenda",
            _apibank_add_agenda_calls("hard agenda", "2026-07-07 18:00:00", "Room H"),
            _agenda_goal("1", "hard agenda", "2026-07-07 18:00:00", "Room H"),
            "hard_schema_drift",
            3,
            "Agenda workflow: hard schema drift is intentionally unrecoverable for current policies.",
        ),
        _apibank_case(
            "add_meeting_timeout",
            "AddMeeting",
            _apibank_add_meeting_calls("project kickoff", "2026-08-01 09:00:00", "2026-08-01 10:00:00", "Room M", ["Ada", "Ben"]),
            _meeting_goal("0", "project kickoff", "2026-08-01 09:00:00", "2026-08-01 10:00:00"),
            "timeout",
            1,
            "Meeting workflow: AddMeeting times out once before persisting meeting state.",
        ),
        _apibank_case(
            "add_meeting_schema_drift",
            "AddMeeting",
            _apibank_add_meeting_calls("paper rehearsal", "2026-08-02 11:00:00", "2026-08-02 12:00:00", "Room R", ["Chen", "Dana"]),
            _meeting_goal("0", "paper rehearsal", "2026-08-02 11:00:00", "2026-08-02 12:00:00"),
            "schema_drift",
            1,
            "Meeting workflow: AddMeeting recovers from schema drift.",
        ),
        _apibank_case(
            "add_meeting_persistent_timeout",
            "AddMeeting",
            _apibank_add_meeting_calls("budget review", "2026-08-03 13:00:00", "2026-08-03 14:00:00", "Room B", ["Eva", "Finn"]),
            _meeting_goal("0", "budget review", "2026-08-03 13:00:00", "2026-08-03 14:00:00"),
            "persistent_timeout",
            2,
            "Meeting workflow: AddMeeting requires stronger retry under persistent timeout.",
        ),
        _apibank_case(
            "add_modify_meeting_timeout",
            "ModifyMeeting",
            _apibank_add_modify_query_meeting_calls(
                "demo prep",
                "2026-08-04 15:00:00",
                "2026-08-04 16:00:00",
                "Room D",
                ["Grace", "Hao"],
                "2026-08-04 17:00:00",
                "2026-08-04 18:00:00",
            ),
            _meeting_goal("0", "demo prep", "2026-08-04 17:00:00", "2026-08-04 18:00:00"),
            "timeout",
            1,
            "Meeting dependency workflow: AddMeeting succeeds, then ModifyMeeting times out once.",
        ),
        _apibank_case(
            "add_modify_meeting_schema_drift",
            "ModifyMeeting",
            _apibank_add_modify_query_meeting_calls(
                "reading group",
                "2026-08-05 10:00:00",
                "2026-08-05 11:00:00",
                "Room G",
                ["Ivy", "Jun"],
                "2026-08-05 12:00:00",
                "2026-08-05 13:00:00",
            ),
            _meeting_goal("0", "reading group", "2026-08-05 12:00:00", "2026-08-05 13:00:00"),
            "schema_drift",
            1,
            "Meeting dependency workflow: ModifyMeeting recovers after schema drift.",
        ),
        _apibank_case(
            "preseeded_modify_meeting_persistent_timeout",
            "ModifyMeeting",
            _apibank_modify_query_meeting_calls(
                "lab planning",
                "2026-08-06 14:00:00",
                "2026-08-06 16:00:00",
                "2026-08-06 17:00:00",
            ),
            _meeting_goal("0", "lab planning", "2026-08-06 16:00:00", "2026-08-06 17:00:00"),
            "persistent_timeout",
            2,
            "Meeting state update workflow: ModifyMeeting acts on a preseeded meeting row.",
            initial_state=_apibank_state(
                meeting={
                    "0": {
                        "username": "foo",
                        "meeting_topic": "lab planning",
                        "start_time": "2026-08-06 14:00:00",
                        "end_time": "2026-08-06 15:00:00",
                        "location": "Room L",
                        "attendees": ["Kai", "Lin"],
                    }
                }
            ),
        ),
        _apibank_case(
            "add_meeting_hard_schema_drift",
            "AddMeeting",
            _apibank_add_meeting_calls("hard meeting", "2026-08-07 18:00:00", "2026-08-07 19:00:00", "Room Z", ["Mia"]),
            _meeting_goal("0", "hard meeting", "2026-08-07 18:00:00", "2026-08-07 19:00:00"),
            "hard_schema_drift",
            3,
            "Meeting workflow: hard schema drift is intentionally unrecoverable for current policies.",
        ),
    ]


def _build_synthetic_semantic_recovery_cases() -> list[BackendMigrationCase]:
    """Synthetic semantic probes that require more than blind retry."""
    return [
        BackendMigrationCase(
            case_name="synthetic_backend::semantic_modify_password_recovery",
            source="synthetic_backend",
            description=(
                "Synthetic semantic probe: direct/cot repeat a wrong old_password, "
                "while react/self_refine switch to a valid recovery path."
            ),
            goals=_account_password_goal("semantic-old-password"),
            target_tool="ModifyPassword",
            live_like_fault="semantic_validation",
            live_like_fault_count=0,
            strategy_tool_calls={
                "direct": [
                    _tool_call(
                        "ModifyPassword",
                        token=_apibank_token(),
                        old_password="definitely-wrong",
                        new_password="semantic-old-password",
                    )
                ],
                "cot": [
                    _tool_call(
                        "ModifyPassword",
                        token=_apibank_token(),
                        old_password="definitely-wrong",
                        new_password="semantic-old-password",
                    ),
                    _tool_call(
                        "ModifyPassword",
                        token=_apibank_token(),
                        old_password="definitely-wrong",
                        new_password="semantic-old-password",
                    ),
                ],
                "react": [
                    _tool_call(
                        "ModifyPassword",
                        token=_apibank_token(),
                        old_password="definitely-wrong",
                        new_password="semantic-old-password",
                    ),
                    _tool_call("GetUserToken", username="foo", password="bar"),
                    _tool_call(
                        "ModifyPassword",
                        token=_apibank_token(),
                        old_password="bar",
                        new_password="semantic-old-password",
                    ),
                ],
                "self_refine": [
                    _tool_call(
                        "ModifyPassword",
                        token=_apibank_token(),
                        old_password="definitely-wrong",
                        new_password="semantic-old-password",
                    ),
                    _tool_call("GetUserToken", username="foo", password="bar"),
                    _tool_call(
                        "ModifyPassword",
                        token=_apibank_token(),
                        old_password="bar",
                        new_password="semantic-old-password",
                    ),
                ],
            },
            initial_state=_apibank_state(),
        ),
        BackendMigrationCase(
            case_name="synthetic_backend::semantic_modify_missing_contact_recovery",
            source="synthetic_backend",
            description=(
                "Synthetic semantic probe: direct/cot try to modify a missing "
                "contact, while react/self_refine create it before retrying the update."
            ),
            goals=[
                {
                    "type": "toolsandbox_record_exists",
                    "entity_type": "contact",
                    "fields": {"person_id": "ghost_contact", "name": "Ghost", "phone_number": "+15550000000"},
                }
            ],
            target_tool="modify_contact",
            live_like_fault="semantic_validation",
            live_like_fault_count=0,
            strategy_tool_calls={
                "direct": [
                    _tool_call("modify_contact", person_id="ghost_contact", name="Ghost", phone_number="+15550000000")
                ],
                "cot": [
                    _tool_call("modify_contact", person_id="ghost_contact", name="Ghost", phone_number="+15550000000"),
                    _tool_call("modify_contact", person_id="ghost_contact", name="Ghost", phone_number="+15550000000"),
                ],
                "react": [
                    _tool_call("modify_contact", person_id="ghost_contact", name="Ghost", phone_number="+15550000000"),
                    _tool_call("add_contact", person_id="ghost_contact", name="Ghost", phone_number="+15550000000"),
                    _tool_call("modify_contact", person_id="ghost_contact", name="Ghost", phone_number="+15550000000"),
                ],
                "self_refine": [
                    _tool_call("modify_contact", person_id="ghost_contact", name="Ghost", phone_number="+15550000000"),
                    _tool_call("add_contact", person_id="ghost_contact", name="Ghost", phone_number="+15550000000"),
                    _tool_call("modify_contact", person_id="ghost_contact", name="Ghost", phone_number="+15550000000"),
                ],
            },
            initial_state=_toolsandbox_base_state(),
        ),
        BackendMigrationCase(
            case_name="synthetic_backend::semantic_add_agenda_time_recovery",
            source="synthetic_backend",
            description=(
                "Synthetic semantic probe: direct/cot use an invalid time string, "
                "while react/self_refine repair the time format."
            ),
            goals=_agenda_goal("1", "semantic agenda", "2026-09-01 09:00:00", "Lab"),
            target_tool="AddAgenda",
            live_like_fault="semantic_validation",
            live_like_fault_count=0,
            strategy_tool_calls={
                "direct": [
                    _tool_call(
                        "AddAgenda",
                        token=_apibank_token(),
                        content="semantic agenda",
                        time="not-a-time",
                        normalized_time="2026-09-01 09:00:00",
                        location="Lab",
                    )
                ],
                "cot": [
                    _tool_call(
                        "AddAgenda",
                        token=_apibank_token(),
                        content="semantic agenda",
                        time="not-a-time",
                        normalized_time="2026-09-01 09:00:00",
                        location="Lab",
                    ),
                    _tool_call(
                        "AddAgenda",
                        token=_apibank_token(),
                        content="semantic agenda",
                        time="not-a-time",
                        normalized_time="2026-09-01 09:00:00",
                        location="Lab",
                    ),
                ],
                "react": [
                    _tool_call("AddAgenda", token=_apibank_token(), content="semantic agenda", time="not-a-time", location="Lab"),
                    _tool_call("AddAgenda", token=_apibank_token(), content="semantic agenda", time="2026-09-01 09:00:00", location="Lab"),
                ],
                "self_refine": [
                    _tool_call("AddAgenda", token=_apibank_token(), content="semantic agenda", time="not-a-time", location="Lab"),
                    _tool_call("AddAgenda", token=_apibank_token(), content="semantic agenda", time="2026-09-01 09:00:00", location="Lab"),
                ],
            },
            initial_state=_apibank_state(),
        ),
    ]


def _build_toolsandbox_cases(path: str | Path, limit: int) -> list[BackendMigrationCase]:
    converted = [
        case for case in convert_toolsandbox_file(path)
        if case.goals and case.oracle_tool_calls
    ]
    selected = _round_robin_by_domain(converted)[:limit]
    cases: list[BackendMigrationCase] = []
    fault_cycle = [
        ("timeout", 1),
        ("schema_drift", 1),
        ("persistent_timeout", 2),
        ("hard_schema_drift", 3),
    ]
    for case in selected:
        fault_type, fault_count = fault_cycle[len(cases) % len(fault_cycle)]
        target_tool = _first_non_terminal_tool(case.oracle_tool_calls)
        cases.append(BackendMigrationCase(
            case_name=f"toolsandbox_backend::{case.scenario_name}",
            source="toolsandbox_backend_subset",
            description=(
                f"ToolSandbox backend migration case from {case.scenario_name}; "
                f"live-like fault={fault_type}:{fault_count}."
            ),
            goals=case.goals,
            target_tool=target_tool,
            live_like_fault=fault_type,
            live_like_fault_count=fault_count,
            strategy_tool_calls=_strategy_calls_with_retry(case.oracle_tool_calls, target_tool),
            initial_state=case.initial_state,
        ))
    return cases


def _strategy_calls_with_retry(tool_calls: list[dict[str, Any]], target_tool: str) -> dict[str, list[dict[str, Any]]]:
    return {
        "direct": tool_calls,
        "cot": _insert_retry_after_first_target(tool_calls, target_tool, retry_count=1),
        "react": _insert_retry_after_first_target(tool_calls, target_tool, retry_count=2),
        "self_refine": _insert_retry_after_first_target(tool_calls, target_tool, retry_count=2),
    }


def _apibank_case(
    name: str,
    target_tool: str,
    calls: list[dict[str, Any]],
    goals: list[dict[str, Any]],
    fault_type: str,
    fault_count: int,
    description: str,
    *,
    initial_state: WorldState | None = None,
) -> BackendMigrationCase:
    return BackendMigrationCase(
        case_name=f"apibank_backend::{name}",
        source="api_bank_backend_subset",
        description=description,
        goals=goals,
        target_tool=target_tool,
        live_like_fault=fault_type,
        live_like_fault_count=fault_count,
        strategy_tool_calls=_strategy_calls_with_retry(calls, target_tool),
        initial_state=initial_state or _apibank_state(),
    )


def _toolsandbox_base_state() -> WorldState:
    state = WorldState()
    ensure_toolsandbox_state(state)
    state.set_entity("contact", "self", {
        "person_id": "self",
        "name": "Self",
        "phone_number": "+10000000000",
        "relationship": None,
        "is_self": True,
    })
    return state


def _apibank_state(
    *,
    account_password: str = "bar",
    agenda: dict[str, dict[str, Any]] | None = None,
    meeting: dict[str, dict[str, Any]] | None = None,
) -> WorldState:
    state = WorldState()
    state.set_entity("account", "foo", {
        "username": "foo",
        "password": account_password,
        "token": _apibank_token(),
        "email": "foo@example.com",
    })
    state.entities["agenda"] = dict(agenda or {})
    state.entities["meeting"] = dict(meeting or {})
    state.policies.setdefault("backend", {})
    state.policies["backend"]["api_bank_runtime"] = APIBANK_RUNTIME_NAME
    return state


def _apibank_token() -> str:
    return "z9x8c7v6b5n4m3q2w1"


def _tool_call(tool_name: str, **args: Any) -> dict[str, Any]:
    return {"tool_name": tool_name, "args": args}


def _apibank_forgot_password_calls(new_password: str) -> list[dict[str, Any]]:
    return [
        _tool_call("ForgotPassword", status="Forgot Password", username="foo", email="foo@example.com"),
        _tool_call("ForgotPassword", status="Verification Code", verification_code=970420, new_password=new_password),
    ]


def _apibank_modify_password_calls(new_password: str) -> list[dict[str, Any]]:
    return [
        _tool_call("GetUserToken", username="foo", password="bar"),
        _tool_call("ModifyPassword", token=_apibank_token(), old_password="bar", new_password=new_password),
        _tool_call("GetUserToken", username="foo", password=new_password),
    ]


def _apibank_check_then_modify_password_calls(new_password: str) -> list[dict[str, Any]]:
    return [
        _tool_call("CheckToken", token=_apibank_token()),
        _tool_call("ModifyPassword", token=_apibank_token(), old_password="bar", new_password=new_password),
        _tool_call("GetUserToken", username="foo", password=new_password),
    ]


def _apibank_add_agenda_calls(content: str, time: str, location: str) -> list[dict[str, Any]]:
    return [
        _tool_call("AddAgenda", token=_apibank_token(), content=content, time=time, location=location),
        _tool_call("QueryAgenda", token=_apibank_token(), content=content, time=time, location=location),
    ]


def _apibank_add_modify_query_agenda_calls(
    content: str,
    initial_time: str,
    initial_location: str,
    new_time: str,
    new_location: str,
) -> list[dict[str, Any]]:
    return [
        _tool_call("AddAgenda", token=_apibank_token(), content=content, time=initial_time, location=initial_location),
        _tool_call("ModifyAgenda", token=_apibank_token(), content=content, time=new_time, location=new_location),
        _tool_call("QueryAgenda", token=_apibank_token(), content=content, time=new_time, location=new_location),
    ]


def _apibank_modify_query_agenda_calls(
    content: str,
    initial_time: str,
    new_time: str,
    new_location: str,
) -> list[dict[str, Any]]:
    return [
        _tool_call("QueryAgenda", token=_apibank_token(), content=content, time=initial_time, location=""),
        _tool_call("ModifyAgenda", token=_apibank_token(), content=content, time=new_time, location=new_location),
        _tool_call("QueryAgenda", token=_apibank_token(), content=content, time=new_time, location=new_location),
    ]


def _apibank_add_meeting_calls(
    topic: str,
    start_time: str,
    end_time: str,
    location: str,
    attendees: list[str],
) -> list[dict[str, Any]]:
    return [
        _tool_call(
            "AddMeeting",
            token=_apibank_token(),
            meeting_topic=topic,
            start_time=start_time,
            end_time=end_time,
            location=location,
            attendees=attendees,
        ),
        _tool_call(
            "QueryMeeting",
            token=_apibank_token(),
            meeting_topic=topic,
            start_time=start_time,
            end_time=end_time,
            location=location,
            attendees=attendees,
        ),
    ]


def _apibank_add_modify_query_meeting_calls(
    topic: str,
    initial_start: str,
    initial_end: str,
    location: str,
    attendees: list[str],
    new_start: str,
    new_end: str,
) -> list[dict[str, Any]]:
    return [
        *_apibank_add_meeting_calls(topic, initial_start, initial_end, location, attendees)[:1],
        _tool_call(
            "ModifyMeeting",
            token=_apibank_token(),
            meeting_topic=topic,
            start_time=new_start,
            end_time=new_end,
            location=location,
            attendees=attendees,
        ),
        _tool_call(
            "QueryMeeting",
            token=_apibank_token(),
            meeting_topic=topic,
            start_time=new_start,
            end_time=new_end,
            location=location,
            attendees=attendees,
        ),
    ]


def _apibank_modify_query_meeting_calls(
    topic: str,
    initial_start: str,
    new_start: str,
    new_end: str,
) -> list[dict[str, Any]]:
    return [
        _tool_call(
            "QueryMeeting",
            token=_apibank_token(),
            meeting_topic=topic,
            start_time=initial_start,
            end_time="",
            location="",
            attendees=[],
        ),
        _tool_call(
            "ModifyMeeting",
            token=_apibank_token(),
            meeting_topic=topic,
            start_time=new_start,
            end_time=new_end,
            location="Room L",
            attendees=["Kai", "Lin"],
        ),
        _tool_call(
            "QueryMeeting",
            token=_apibank_token(),
            meeting_topic=topic,
            start_time=new_start,
            end_time=new_end,
            location="Room L",
            attendees=["Kai", "Lin"],
        ),
    ]


def _account_password_goal(expected_password: str) -> list[dict[str, Any]]:
    return [
        {
            "type": "entity_field_equals",
            "entity_type": "account",
            "entity_id": "foo",
            "field": "password",
            "expected": expected_password,
        }
    ]


def _forgot_password_goals(expected_password: str) -> list[dict[str, Any]]:
    return [
        *_account_password_goal(expected_password),
        {
            "type": "entity_field_equals",
            "entity_type": "password_reset",
            "entity_id": "current",
            "field": "consumed",
            "expected": True,
        },
    ]


def _agenda_goal(entity_id: str, content: str, time: str, location: str) -> list[dict[str, Any]]:
    return [
        {"type": "entity_field_equals", "entity_type": "agenda", "entity_id": entity_id, "field": "content", "expected": content},
        {"type": "entity_field_equals", "entity_type": "agenda", "entity_id": entity_id, "field": "time", "expected": time},
        {"type": "entity_field_equals", "entity_type": "agenda", "entity_id": entity_id, "field": "location", "expected": location},
    ]


def _meeting_goal(entity_id: str, topic: str, start_time: str, end_time: str) -> list[dict[str, Any]]:
    return [
        {"type": "entity_field_equals", "entity_type": "meeting", "entity_id": entity_id, "field": "meeting_topic", "expected": topic},
        {"type": "entity_field_equals", "entity_type": "meeting", "entity_id": entity_id, "field": "start_time", "expected": start_time},
        {"type": "entity_field_equals", "entity_type": "meeting", "entity_id": entity_id, "field": "end_time", "expected": end_time},
    ]


def _fault_profile_for_backend(case: BackendMigrationCase, backend_name: str) -> FaultProfile:
    if backend_name == "sandbox":
        return FaultProfile(latency_ms_by_tool={case.target_tool: 2})
    if backend_name == "live_like":
        if case.live_like_fault in {"timeout", "persistent_timeout"}:
            return FaultProfile(
                timeout_failures={case.target_tool: case.live_like_fault_count},
                latency_ms_by_tool={case.target_tool: 5},
            )
        if case.live_like_fault in {"schema_drift", "hard_schema_drift"}:
            return FaultProfile(
                schema_drift_failures={case.target_tool: case.live_like_fault_count},
                latency_ms_by_tool={case.target_tool: 5},
            )
        return FaultProfile(
            timeout_failures={case.target_tool: 1},
            latency_ms_by_tool={case.target_tool: 5},
        )
    return FaultProfile()


def _backend_for_name(backend_name: str, case_name: str) -> BaseBackend:
    session_id = case_name.replace("::", "_").replace(" ", "_")[:40]
    if backend_name == "sandbox":
        return SandboxBackend(session_id=f"sandbox_{session_id}")
    if backend_name == "live_like":
        return LiveLikeBackend(session_id=f"live_{session_id}")
    return MockBackend()


def _compute_group_metrics(
    results: list[BackendMigrationRunResult],
    strategies: list[str],
    backends: list[str],
) -> list[BackendMigrationGroupMetrics]:
    mock_success = {
        strategy: _rate(
            sum(1 for result in results if result.strategy == strategy and result.backend == "mock" and result.final_state_correct),
            sum(1 for result in results if result.strategy == strategy and result.backend == "mock"),
        )
        for strategy in strategies
    }
    metrics: list[BackendMigrationGroupMetrics] = []
    for strategy in strategies:
        for backend in backends:
            group = [result for result in results if result.strategy == strategy and result.backend == backend]
            total = len(group)
            final_correct = _rate(sum(1 for result in group if result.final_state_correct), total)
            recovery_opportunities = sum(1 for result in group if result.result.call_metrics.failed_calls > 0)
            metrics.append(BackendMigrationGroupMetrics(
                strategy=strategy,
                backend=backend,
                total_cases=total,
                final_state_correctness=final_correct,
                migration_gap=max(0.0, mock_success[strategy] - final_correct),
                state_divergence_rate=_rate(sum(1 for result in group if result.state_diverged_from_mock), total),
                invalid_call_rate=_rate(sum(result.invalid_call_rate for result in group), total),
                recovery_rate=_rate(sum(1 for result in group if result.recovery_detected), recovery_opportunities),
                average_trajectory_length=_rate(sum(result.trajectory_length for result in group), total),
                average_latency_ms=_rate(sum(result.latency_ms for result in group), total),
            ))
    return metrics


def _build_interpretation(result: BackendMigrationResult) -> str:
    live_metrics = [metric for metric in result.group_metrics if metric.backend == "live_like"]
    if not live_metrics:
        return "No live-like backend results were available."
    worst = max(live_metrics, key=lambda metric: metric.migration_gap)
    best = min(live_metrics, key=lambda metric: metric.migration_gap)
    return (
        f"The largest mock-to-live-like migration gap appears for `{worst.strategy}`, "
        f"while `{best.strategy}` transfers most robustly. This suggests that backend realism "
        "can reveal failures hidden by purely in-memory mock execution."
    )


def _insert_retry_after_first_target(
    tool_calls: list[dict[str, Any]],
    target_tool: str,
    *,
    retry_count: int,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    inserted = False
    for call in tool_calls:
        result.append(call)
        if not inserted and call.get("tool_name") == target_tool:
            for _ in range(retry_count):
                result.append({"tool_name": call.get("tool_name"), "args": dict(call.get("args") or {})})
            inserted = True
    return result


def _first_non_terminal_tool(tool_calls: list[dict[str, Any]]) -> str:
    for call in tool_calls:
        tool_name = str(call.get("tool_name", ""))
        if tool_name and tool_name != "end_conversation":
            return tool_name
    return str(tool_calls[0].get("tool_name", ""))


def _round_robin_by_domain(cases: list[Any]) -> list[Any]:
    by_domain: dict[str, list[Any]] = {}
    for case in sorted(cases, key=lambda item: (item.domain, item.scenario_name)):
        by_domain.setdefault(case.domain or "unknown", []).append(case)

    result: list[Any] = []
    while any(by_domain.values()):
        for domain in sorted(by_domain):
            if by_domain[domain]:
                result.append(by_domain[domain].pop(0))
    return result


def _clone_state(state: WorldState) -> WorldState:
    return WorldState.from_dict(state.to_dict())


def _default_toolsandbox_path() -> Path:
    if env_path := os.environ.get("AGENTINFERKIT_TOOLSANDBOX_PATH"):
        return Path(env_path)
    return Path(__file__).resolve().parents[3] / "Toolsandbox" / "tool_sandbox_scenarios.json"


def _pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def _rate(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0
