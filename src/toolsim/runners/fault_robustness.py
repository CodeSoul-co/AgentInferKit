"""Fault robustness comparison runner.

Runs clean and faulted variants of the same stateful tool task, then summarizes
whether the task still reaches its final state goals under structured faults.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from toolsim.adapters.toolsandbox_adapter import convert_toolsandbox_file
from toolsim.core.world_state import WorldState
from toolsim.execution.stateful_executor import ExecutorConfig
from toolsim.faults import FaultProfile
from toolsim.runners.comparison_runner import (
    ComparisonCase,
    build_stateless_vs_stateful_cases,
    build_toolsandbox_stateless_vs_stateful_cases,
    select_toolsandbox_comparison_subset_cases,
)
from toolsim.runners.experiment_runner import ExperimentResult, ExperimentRunner

NOISE_TIMEOUT = "timeout"
NOISE_SCHEMA_DRIFT = "schema_drift"
NOISE_STALE_STATE = "stale_state"
NOISE_VAGUE_OBSERVATION = "vague_observation"
DEFAULT_NOISE_TYPES = [NOISE_TIMEOUT, NOISE_SCHEMA_DRIFT, NOISE_STALE_STATE, NOISE_VAGUE_OBSERVATION]


@dataclass
class FaultRobustnessCase:
    case_name: str
    description: str
    clean_tool_calls: list[dict[str, Any]]
    fault_tool_calls: list[dict[str, Any]]
    goals: list[dict[str, Any]]
    fault_profile: FaultProfile
    noise_type: str = "generic"
    source: str = "synthetic"
    success_at_1_tool_calls: list[dict[str, Any]] | None = None
    pass_k_tool_calls: list[dict[str, Any]] | None = None
    k: int = 2
    permissions: set[str] | None = None
    clean_initial_state: WorldState | None = None
    fault_initial_state: WorldState | None = None


@dataclass
class FaultRobustnessCaseResult:
    case: FaultRobustnessCase
    clean_result: ExperimentResult
    success_at_1_result: ExperimentResult
    fault_result: ExperimentResult
    success_at_1: bool
    pass_k_success: bool
    final_success: bool
    clean_success: bool
    recovery_detected: bool
    state_corrupted: bool
    extra_steps: int
    cost_increase: int
    failed_fault_calls: int
    observation_fault_count: int
    clean_latency_ms: float
    fault_latency_ms: float
    latency_increase_ms: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_name": self.case.case_name,
            "description": self.case.description,
            "noise_type": self.case.noise_type,
            "source": self.case.source,
            "k": self.case.k,
            "success_at_1": self.success_at_1,
            "pass_k_success": self.pass_k_success,
            "final_success": self.final_success,
            "clean_success": self.clean_success,
            "recovery_detected": self.recovery_detected,
            "state_corrupted": self.state_corrupted,
            "extra_steps": self.extra_steps,
            "cost_increase": self.cost_increase,
            "failed_fault_calls": self.failed_fault_calls,
            "observation_fault_count": self.observation_fault_count,
            "clean_latency_ms": self.clean_latency_ms,
            "fault_latency_ms": self.fault_latency_ms,
            "latency_increase_ms": self.latency_increase_ms,
            "clean_result": self.clean_result.to_dict(),
            "success_at_1_result": self.success_at_1_result.to_dict(),
            "fault_result": self.fault_result.to_dict(),
        }


@dataclass
class FaultRobustnessMetrics:
    total_cases: int
    final_success_count: int
    failure_case_count: int
    recovered_case_count: int
    state_corruption_count: int
    success_at_1_count: int
    pass_k_success_count: int
    success_rate: float
    success_at_1: float
    pass_k: float
    recovery_rate: float
    state_corruption_rate: float
    average_extra_steps: float
    average_cost_increase: float
    average_latency_increase_ms: float
    by_noise_type: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_cases": self.total_cases,
            "final_success_count": self.final_success_count,
            "failure_case_count": self.failure_case_count,
            "recovered_case_count": self.recovered_case_count,
            "state_corruption_count": self.state_corruption_count,
            "success_at_1_count": self.success_at_1_count,
            "pass_k_success_count": self.pass_k_success_count,
            "success_rate": self.success_rate,
            "success_at_1": self.success_at_1,
            "pass_k": self.pass_k,
            "recovery_rate": self.recovery_rate,
            "state_corruption_rate": self.state_corruption_rate,
            "average_extra_steps": self.average_extra_steps,
            "average_cost_increase": self.average_cost_increase,
            "average_latency_increase_ms": self.average_latency_increase_ms,
            "by_noise_type": self.by_noise_type,
        }


@dataclass
class FaultRobustnessBatchResult:
    results: list[FaultRobustnessCaseResult] = field(default_factory=list)
    metrics: FaultRobustnessMetrics | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "metrics": self.metrics.to_dict() if self.metrics is not None else None,
            "results": [result.to_dict() for result in self.results],
        }


class FaultRobustnessRunner:
    """Run clean-vs-faulted stateful tool robustness cases."""

    def run_case(self, case: FaultRobustnessCase) -> FaultRobustnessCaseResult:
        clean_result = ExperimentRunner().run(
            tool_calls=case.clean_tool_calls,
            initial_state=_clone_state(case.clean_initial_state) if case.clean_initial_state is not None else WorldState(),
            goals=case.goals,
            permissions=case.permissions,
        )
        success_at_1_result = ExperimentRunner(
            executor_config=ExecutorConfig(fault_profile=case.fault_profile)
        ).run(
            tool_calls=case.success_at_1_tool_calls or case.fault_tool_calls,
            initial_state=_clone_state(case.fault_initial_state) if case.fault_initial_state is not None else WorldState(),
            goals=case.goals,
            permissions=case.permissions,
        )
        fault_result = ExperimentRunner(
            executor_config=ExecutorConfig(fault_profile=case.fault_profile)
        ).run(
            tool_calls=case.pass_k_tool_calls or case.fault_tool_calls,
            initial_state=_clone_state(case.fault_initial_state) if case.fault_initial_state is not None else WorldState(),
            goals=case.goals,
            permissions=case.permissions,
        )

        clean_success = _goals_passed(clean_result)
        success_at_1 = _goals_passed(success_at_1_result)
        final_success = _goals_passed(fault_result)
        failed_fault_calls = sum(1 for record in fault_result.trace if not record.success)
        failed_at_1_calls = sum(1 for record in success_at_1_result.trace if not record.success)
        recovered = (failed_at_1_calls > 0 or not success_at_1) and final_success
        clean_latency = _total_latency(clean_result)
        fault_latency = _total_latency(fault_result)

        return FaultRobustnessCaseResult(
            case=case,
            clean_result=clean_result,
            success_at_1_result=success_at_1_result,
            fault_result=fault_result,
            success_at_1=success_at_1,
            pass_k_success=final_success,
            final_success=final_success,
            clean_success=clean_success,
            recovery_detected=recovered,
            state_corrupted=not final_success,
            extra_steps=len(fault_result.trace) - len(clean_result.trace),
            cost_increase=len(fault_result.trace) - len(clean_result.trace),
            failed_fault_calls=failed_fault_calls,
            observation_fault_count=sum(1 for record in fault_result.trace if "fault" in record.metadata),
            clean_latency_ms=clean_latency,
            fault_latency_ms=fault_latency,
            latency_increase_ms=fault_latency - clean_latency,
        )

    def run(self, cases: list[FaultRobustnessCase]) -> FaultRobustnessBatchResult:
        results = [self.run_case(case) for case in cases]
        return FaultRobustnessBatchResult(results=results, metrics=_compute_metrics(results))


def build_default_fault_robustness_cases() -> list[FaultRobustnessCase]:
    """Build a compact default suite for the first robustness report."""
    return [
        FaultRobustnessCase(
            case_name="latency_file_write",
            description="Artificial latency is injected into file.write without changing the final state.",
            clean_tool_calls=[
                {"tool_name": "file.write", "args": {"file_id": "f1", "content": "hello"}},
            ],
            fault_tool_calls=[
                {"tool_name": "file.write", "args": {"file_id": "f1", "content": "hello"}},
            ],
            goals=[
                {"type": "entity_field_equals", "entity_type": "file", "entity_id": "f1", "field": "content", "expected": "hello"},
            ],
            fault_profile=FaultProfile(latency_ms_by_tool={"file.write": 5}),
            permissions={"file.write"},
        ),
        FaultRobustnessCase(
            case_name="transient_file_write_recovery",
            description="The first file.write fails transiently; a retry recovers the final state.",
            clean_tool_calls=[
                {"tool_name": "file.write", "args": {"file_id": "f1", "content": "hello"}},
            ],
            fault_tool_calls=[
                {"tool_name": "file.write", "args": {"file_id": "f1", "content": "hello"}},
                {"tool_name": "file.write", "args": {"file_id": "f1", "content": "hello"}},
            ],
            success_at_1_tool_calls=[
                {"tool_name": "file.write", "args": {"file_id": "f1", "content": "hello"}},
            ],
            goals=[
                {"type": "entity_field_equals", "entity_type": "file", "entity_id": "f1", "field": "content", "expected": "hello"},
            ],
            fault_profile=FaultProfile(transient_failures={"file.write": 1}),
            permissions={"file.write"},
        ),
        FaultRobustnessCase(
            case_name="stale_search_observation",
            description="The second search.query replays a stale observation while the index state itself is current.",
            clean_tool_calls=[
                {"tool_name": "file.write", "args": {"file_id": "f1", "content": "old hello"}},
                {"tool_name": "search.index", "args": {"file_id": "f1"}},
                {"tool_name": "search.query", "args": {"query": "hello"}},
                {"tool_name": "file.write", "args": {"file_id": "f1", "content": "new gamma"}},
                {"tool_name": "search.index", "args": {"file_id": "f1"}},
                {"tool_name": "search.query", "args": {"query": "gamma"}},
            ],
            fault_tool_calls=[
                {"tool_name": "file.write", "args": {"file_id": "f1", "content": "old hello"}},
                {"tool_name": "search.index", "args": {"file_id": "f1"}},
                {"tool_name": "search.query", "args": {"query": "hello"}},
                {"tool_name": "file.write", "args": {"file_id": "f1", "content": "new gamma"}},
                {"tool_name": "search.index", "args": {"file_id": "f1"}},
                {"tool_name": "search.query", "args": {"query": "gamma"}},
            ],
            goals=[
                {"type": "indexed_contains", "file_id": "f1", "substring": "gamma"},
                {"type": "query_hits_file", "query": "gamma", "file_id": "f1"},
            ],
            fault_profile=FaultProfile(stale_observation_tools={"search.query"}),
            permissions={"file.write", "search.index", "search.query"},
        ),
        FaultRobustnessCase(
            case_name="vague_issue_error_recovery",
            description="A close-before-assignment error is masked, then assignment and retry recover the workflow.",
            clean_tool_calls=[
                {"tool_name": "issue.create", "args": {"issue_id": "iss1", "title": "Bug"}},
                {"tool_name": "issue.assign", "args": {"issue_id": "iss1", "assignee": "bob"}},
                {"tool_name": "issue.close", "args": {"issue_id": "iss1", "resolution": "fixed"}},
            ],
            fault_tool_calls=[
                {"tool_name": "issue.create", "args": {"issue_id": "iss1", "title": "Bug"}},
                {"tool_name": "issue.close", "args": {"issue_id": "iss1", "resolution": "fixed"}},
                {"tool_name": "issue.assign", "args": {"issue_id": "iss1", "assignee": "bob"}},
                {"tool_name": "issue.close", "args": {"issue_id": "iss1", "resolution": "fixed"}},
            ],
            success_at_1_tool_calls=[
                {"tool_name": "issue.create", "args": {"issue_id": "iss1", "title": "Bug"}},
                {"tool_name": "issue.close", "args": {"issue_id": "iss1", "resolution": "fixed"}},
            ],
            goals=[
                {"type": "issue_status_is", "issue_id": "iss1", "status": "closed"},
                {"type": "issue_has_assignee", "issue_id": "iss1", "assignee": "bob"},
            ],
            fault_profile=FaultProfile(vague_error_tools={"issue.close"}),
            permissions={"issue.create", "issue.assign", "issue.close"},
        ),
    ]


def build_experiment1_noise_robustness_cases(
    *,
    toolsandbox_path: str | Path | None = None,
    toolsandbox_per_group: int = 5,
    include_synthetic: bool = True,
    include_toolsandbox: bool = True,
) -> list[FaultRobustnessCase]:
    """Build noise-robustness cases using the same datasets as experiment 1.

    The clean trajectory is the experiment-1 stateful trajectory. The noisy
    success@1 trajectory runs that same trajectory with one injected fault. The
    pass^k trajectory inserts a single retry immediately after the first noisy
    target call.
    """
    cases: list[FaultRobustnessCase] = []
    if include_synthetic:
        cases.extend(build_noise_cases_from_comparison_cases(
            build_stateless_vs_stateful_cases(),
            source="experiment1_synthetic",
        ))

    if include_toolsandbox:
        input_path = Path(toolsandbox_path) if toolsandbox_path is not None else _default_toolsandbox_path()
        source_cases = [case for case in convert_toolsandbox_file(input_path) if case.goals]
        subset = select_toolsandbox_comparison_subset_cases(
            source_cases,
            group_by="domain",
            per_group=toolsandbox_per_group,
        )
        cases.extend(build_noise_cases_from_comparison_cases(
            build_toolsandbox_stateless_vs_stateful_cases(subset),
            source="experiment1_toolsandbox_subset",
        ))
    return cases


def build_noise_cases_from_comparison_cases(
    comparison_cases: list[ComparisonCase],
    *,
    source: str,
    noise_types: list[str] | None = None,
) -> list[FaultRobustnessCase]:
    """Convert experiment-1 comparison cases into stateful noise cases."""
    selected_noise_types = noise_types or DEFAULT_NOISE_TYPES
    cases: list[FaultRobustnessCase] = []
    for comparison_case in comparison_cases:
        stateful_calls = comparison_case.stateful_tool_calls
        goals = comparison_case.goals_stateful or []
        if not stateful_calls or not goals:
            continue
        for noise_type in selected_noise_types:
            target_tool = _target_tool_for_noise(stateful_calls, noise_type)
            if target_tool is None:
                continue
            pass_k_calls = (
                _insert_retry_after_first_target(stateful_calls, target_tool)
                if noise_type in {NOISE_TIMEOUT, NOISE_SCHEMA_DRIFT}
                else stateful_calls
            )
            cases.append(FaultRobustnessCase(
                case_name=f"{source}::{comparison_case.case_name}::{noise_type}",
                description=(
                    f"{comparison_case.description} Noise type={noise_type}; target tool={target_tool}."
                ),
                clean_tool_calls=stateful_calls,
                fault_tool_calls=pass_k_calls,
                success_at_1_tool_calls=stateful_calls,
                pass_k_tool_calls=pass_k_calls,
                goals=goals,
                fault_profile=_profile_for_noise(noise_type, target_tool),
                noise_type=noise_type,
                source=source,
                k=2,
                clean_initial_state=comparison_case.initial_state_stateful,
                fault_initial_state=comparison_case.initial_state_stateful,
            ))
    return cases


def _compute_metrics(results: list[FaultRobustnessCaseResult]) -> FaultRobustnessMetrics:
    total = len(results)
    final_success_count = sum(1 for result in results if result.final_success)
    failure_case_count = sum(1 for result in results if result.failed_fault_calls > 0)
    recovered_case_count = sum(1 for result in results if result.recovery_detected)
    state_corruption_count = sum(1 for result in results if result.state_corrupted)
    success_at_1_count = sum(1 for result in results if result.success_at_1)
    pass_k_success_count = sum(1 for result in results if result.pass_k_success)

    return FaultRobustnessMetrics(
        total_cases=total,
        final_success_count=final_success_count,
        failure_case_count=failure_case_count,
        recovered_case_count=recovered_case_count,
        state_corruption_count=state_corruption_count,
        success_at_1_count=success_at_1_count,
        pass_k_success_count=pass_k_success_count,
        success_rate=(final_success_count / total) if total else 0.0,
        success_at_1=(success_at_1_count / total) if total else 0.0,
        pass_k=(pass_k_success_count / total) if total else 0.0,
        recovery_rate=(recovered_case_count / failure_case_count) if failure_case_count else 0.0,
        state_corruption_rate=(state_corruption_count / total) if total else 0.0,
        average_extra_steps=(sum(result.extra_steps for result in results) / total) if total else 0.0,
        average_cost_increase=(sum(result.cost_increase for result in results) / total) if total else 0.0,
        average_latency_increase_ms=(sum(result.latency_increase_ms for result in results) / total) if total else 0.0,
        by_noise_type=_compute_noise_type_metrics(results),
    )


def _goals_passed(result: ExperimentResult) -> bool:
    return result.state_metrics is not None and result.state_metrics.all_passed


def _total_latency(result: ExperimentResult) -> float:
    return sum(record.duration_ms for record in result.trace)


def _clone_state(state: WorldState) -> WorldState:
    return WorldState.from_dict(state.to_dict())


def _default_toolsandbox_path() -> Path:
    return Path(__file__).resolve().parents[3] / "Toolsandbox" / "tool_sandbox_scenarios.json"


def _target_tool_for_noise(tool_calls: list[dict[str, Any]], noise_type: str) -> str | None:
    tool_names = [str(call.get("tool_name", "")) for call in tool_calls if call.get("tool_name")]
    non_terminal = [tool_name for tool_name in tool_names if tool_name != "end_conversation"]
    if not non_terminal:
        return tool_names[0] if tool_names else None

    if noise_type in {NOISE_STALE_STATE, NOISE_VAGUE_OBSERVATION}:
        for tool_name in non_terminal:
            if _is_observation_tool(tool_name):
                return tool_name
    return non_terminal[0]


def _is_observation_tool(tool_name: str) -> bool:
    return (
        "search" in tool_name
        or tool_name.startswith("get_")
        or tool_name.endswith(".read")
        or tool_name.endswith(".query")
        or tool_name.endswith("search_events")
    )


def _profile_for_noise(noise_type: str, target_tool: str) -> FaultProfile:
    if noise_type == NOISE_TIMEOUT:
        return FaultProfile(timeout_failures={target_tool: 1}, latency_ms_by_tool={target_tool: 5})
    if noise_type == NOISE_SCHEMA_DRIFT:
        return FaultProfile(schema_drift_failures={target_tool: 1})
    if noise_type == NOISE_STALE_STATE:
        return FaultProfile(stale_observation_tools={target_tool}, vague_observation_tools={target_tool})
    if noise_type == NOISE_VAGUE_OBSERVATION:
        return FaultProfile(vague_observation_tools={target_tool}, vague_error_tools={target_tool})
    return FaultProfile(transient_failures={target_tool: 1})


def _insert_retry_after_first_target(tool_calls: list[dict[str, Any]], target_tool: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    inserted = False
    for call in tool_calls:
        result.append(call)
        if not inserted and call.get("tool_name") == target_tool:
            result.append({"tool_name": call.get("tool_name"), "args": dict(call.get("args") or {})})
            inserted = True
    return result


def _compute_noise_type_metrics(results: list[FaultRobustnessCaseResult]) -> dict[str, dict[str, Any]]:
    by_noise: dict[str, list[FaultRobustnessCaseResult]] = {}
    for result in results:
        by_noise.setdefault(result.case.noise_type, []).append(result)

    metrics: dict[str, dict[str, Any]] = {}
    for noise_type, group in sorted(by_noise.items()):
        total = len(group)
        failure_cases = sum(1 for result in group if result.failed_fault_calls > 0)
        recovered = sum(1 for result in group if result.recovery_detected)
        metrics[noise_type] = {
            "total_cases": total,
            "success_at_1": _rate(sum(1 for result in group if result.success_at_1), total),
            "pass_k": _rate(sum(1 for result in group if result.pass_k_success), total),
            "recovery_rate": _rate(recovered, failure_cases),
            "average_cost_increase": _rate(sum(result.cost_increase for result in group), total),
            "state_corruption_rate": _rate(sum(1 for result in group if result.state_corrupted), total),
            "average_latency_increase_ms": _rate(sum(result.latency_increase_ms for result in group), total),
        }
    return metrics


def _rate(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0
