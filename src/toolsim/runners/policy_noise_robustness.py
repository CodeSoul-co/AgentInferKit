"""Closed-loop policy noise robustness experiments.

Unlike the fixed-trajectory fault robustness runner, this module lets a policy
choose the next tool call from previous observations. The policies are
deterministic templates for reproducible direct / CoT / ReAct / self-refine
comparisons without requiring live LLM calls.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from toolsim.adapters.toolsandbox_adapter import convert_toolsandbox_file
from toolsim.backends.mock_backend import MockBackend
from toolsim.core.environment import ToolEnvironment
from toolsim.core.trace_state import TraceState
from toolsim.evaluators.evaluator import CallLevelEvaluator, StateLevelEvaluator
from toolsim.execution.stateful_executor import ExecutorConfig, ExecutionRecord, StatefulExecutor, create_default_tool_registry
from toolsim.execution.stateful_tracer import TraceRecorder
from toolsim.faults import FaultProfile
from toolsim.runners.experiment_runner import ExperimentResult
from toolsim.tools.toolsandbox_runtime import ensure_toolsandbox_state

POLICY_STRATEGIES = ["direct", "cot", "react", "self_refine"]
POLICY_NOISE_TYPES = ["timeout", "schema_drift", "stale_state", "vague_observation", "misleading_observation"]


@dataclass
class PolicyNoiseCase:
    case_name: str
    noise_type: str
    task_kind: str
    description: str
    goals: list[dict[str, Any]]
    fault_profile: FaultProfile
    payload: dict[str, Any] = field(default_factory=dict)
    initial_state: TraceState = field(default_factory=TraceState)
    source: str = "synthetic"
    intensity: int = 1
    intensity_label: str = "level_1"
    k: int = 3


@dataclass
class PolicyNoiseRunResult:
    case_name: str
    noise_type: str
    strategy: str
    source: str
    intensity: int
    intensity_label: str
    clean_result: ExperimentResult
    success_at_1_result: ExperimentResult
    pass_k_result: ExperimentResult
    clean_success: bool
    success_at_1: bool
    pass_k_success: bool
    recovery_detected: bool
    cost_increase: int
    state_corrupted: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_name": self.case_name,
            "noise_type": self.noise_type,
            "strategy": self.strategy,
            "source": self.source,
            "intensity": self.intensity,
            "intensity_label": self.intensity_label,
            "clean_success": self.clean_success,
            "success_at_1": self.success_at_1,
            "pass_k_success": self.pass_k_success,
            "recovery_detected": self.recovery_detected,
            "cost_increase": self.cost_increase,
            "state_corrupted": self.state_corrupted,
            "clean_result": self.clean_result.to_dict(),
            "success_at_1_result": self.success_at_1_result.to_dict(),
            "pass_k_result": self.pass_k_result.to_dict(),
        }


@dataclass
class PolicyNoiseGroupMetrics:
    strategy: str
    noise_type: str
    total_cases: int
    success_at_1: float
    pass_k: float
    recovery_rate: float
    average_cost_increase: float
    state_corruption_rate: float
    intensity_label: str = "all"

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy": self.strategy,
            "noise_type": self.noise_type,
            "total_cases": self.total_cases,
            "success_at_1": self.success_at_1,
            "pass_k": self.pass_k,
            "recovery_rate": self.recovery_rate,
            "average_cost_increase": self.average_cost_increase,
            "state_corruption_rate": self.state_corruption_rate,
            "intensity_label": self.intensity_label,
        }


@dataclass
class PolicyNoiseResult:
    results: list[PolicyNoiseRunResult]
    group_metrics: list[PolicyNoiseGroupMetrics]
    intensity_metrics: list[PolicyNoiseGroupMetrics] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "results": [result.to_dict() for result in self.results],
            "group_metrics": [metric.to_dict() for metric in self.group_metrics],
            "intensity_metrics": [metric.to_dict() for metric in self.intensity_metrics],
        }


class PolicyNoiseRobustnessRunner:
    """Run deterministic closed-loop policies under injected stateful noise."""

    def run(
        self,
        cases: list[PolicyNoiseCase],
        strategies: list[str] | None = None,
    ) -> PolicyNoiseResult:
        selected_strategies = strategies or POLICY_STRATEGIES
        results: list[PolicyNoiseRunResult] = []
        for case in cases:
            for strategy in selected_strategies:
                results.append(self.run_case(case, strategy))
        return PolicyNoiseResult(
            results=results,
            group_metrics=_compute_group_metrics(results, selected_strategies),
            intensity_metrics=_compute_intensity_metrics(results, selected_strategies),
        )

    def run_case(self, case: PolicyNoiseCase, strategy: str) -> PolicyNoiseRunResult:
        clean_result = _run_policy(case, strategy, fault_profile=None, allow_recovery=True)
        success_at_1_result = _run_policy(case, strategy, fault_profile=case.fault_profile, allow_recovery=False)
        pass_k_result = _run_policy(case, strategy, fault_profile=case.fault_profile, allow_recovery=True)

        clean_success = _goals_passed(clean_result)
        success_at_1 = _goals_passed(success_at_1_result)
        pass_k_success = _goals_passed(pass_k_result)
        recovery_detected = not success_at_1 and pass_k_success

        return PolicyNoiseRunResult(
            case_name=case.case_name,
            noise_type=case.noise_type,
            strategy=strategy,
            source=case.source,
            intensity=case.intensity,
            intensity_label=case.intensity_label,
            clean_result=clean_result,
            success_at_1_result=success_at_1_result,
            pass_k_result=pass_k_result,
            clean_success=clean_success,
            success_at_1=success_at_1,
            pass_k_success=pass_k_success,
            recovery_detected=recovery_detected,
            cost_increase=max(0, len(pass_k_result.trace) - len(clean_result.trace)),
            state_corrupted=not pass_k_success,
        )


def build_policy_noise_robustness_cases(
    *,
    include_synthetic: bool = True,
    include_toolsandbox: bool = True,
    toolsandbox_path: str | Path | None = None,
    toolsandbox_limit: int | None = None,
    toolsandbox_per_domain: int = 8,
) -> list[PolicyNoiseCase]:
    """Build policy-facing cases with synthetic and ToolSandbox-derived tasks."""
    cases: list[PolicyNoiseCase] = []
    if include_synthetic:
        cases.extend(_build_synthetic_policy_noise_cases())
    if include_toolsandbox:
        input_path = Path(toolsandbox_path) if toolsandbox_path is not None else _default_toolsandbox_path()
        if input_path.exists():
            cases.extend(build_toolsandbox_policy_noise_cases(
                input_path,
                limit=toolsandbox_limit,
                per_domain=toolsandbox_per_domain,
            ))
        elif toolsandbox_path is not None:
            raise FileNotFoundError(input_path)
    return cases


def build_toolsandbox_policy_noise_cases(
    path: str | Path,
    *,
    limit: int | None = None,
    per_domain: int = 8,
) -> list[PolicyNoiseCase]:
    """Build closed-loop policy cases from real converted ToolSandbox scenarios."""
    if not 5 <= per_domain <= 10:
        raise ValueError("per_domain must be between 5 and 10")

    converted = [
        case for case in convert_toolsandbox_file(path)
        if case.goals and len(case.oracle_tool_calls) >= 1
    ]
    selected = _select_toolsandbox_policy_subset(converted, per_domain=per_domain)
    if limit is not None:
        selected = selected[:limit]

    noise_cycle = ["timeout", "schema_drift", "vague_observation", "misleading_observation", "stale_state"]
    cases: list[PolicyNoiseCase] = []
    for index, case in enumerate(selected):
        noise_type = noise_cycle[index % len(noise_cycle)]
        target_tool = _first_observation_tool(case.oracle_tool_calls) or case.oracle_tool_calls[0]["tool_name"]
        cases.append(PolicyNoiseCase(
            case_name=f"toolsandbox_policy::{case.scenario_name}::{noise_type}",
            noise_type=noise_type,
            task_kind="oracle_replay",
            description=f"ToolSandbox policy case from {case.scenario_name}; noise target={target_tool}.",
            goals=case.goals,
            fault_profile=_profile_for_policy_noise(noise_type, target_tool, intensity=1),
            payload={"oracle_tool_calls": case.oracle_tool_calls, "target_tool": target_tool},
            initial_state=case.initial_state,
            source="toolsandbox_policy_subset",
            intensity=1,
            intensity_label="level_1",
            k=3,
        ))
    return cases


def _build_synthetic_policy_noise_cases() -> list[PolicyNoiseCase]:
    cases: list[PolicyNoiseCase] = []
    single_call_templates = [
        (
            "file_write",
            {"tool_name": "file.write", "args": {"file_id": "noise_file", "content": "ready"}},
            [{"type": "entity_field_equals", "entity_type": "file", "entity_id": "noise_file", "field": "content", "expected": "ready"}],
            TraceState(),
        ),
        (
            "issue_create",
            {"tool_name": "issue.create", "args": {"issue_id": "noise_issue", "title": "Bug"}},
            [{"type": "issue_status_is", "issue_id": "noise_issue", "status": "open"}],
            TraceState(),
        ),
        (
            "calendar_create",
            {"tool_name": "calendar.create_event", "args": {"event_id": "noise_event", "title": "Sync", "start_time": 14.0, "end_time": 15.0, "participants": ["ana"]}},
            [{"type": "event_exists", "event_id": "noise_event"}],
            TraceState(),
        ),
        (
            "contact_add",
            {"tool_name": "add_contact", "args": {"person_id": "noise_person", "name": "Mira", "phone_number": "+111"}},
            [{"type": "toolsandbox_record_exists", "entity_type": "contact", "fields": {"name": "Mira", "phone_number": "+111"}}],
            TraceState(),
        ),
        (
            "wifi_setting",
            {"tool_name": "set_wifi_status", "args": {"wifi": True}},
            [{"type": "toolsandbox_setting_equals", "field": "wifi", "expected": True}],
            TraceState(),
        ),
    ]

    for noise_type in ["timeout", "schema_drift"]:
        for intensity in [1, 2, 3]:
            for name, call, goals, state in single_call_templates:
                target_tool = call["tool_name"]
                cases.append(PolicyNoiseCase(
                    case_name=f"synthetic_policy::{name}::{noise_type}::level_{intensity}",
                    noise_type=noise_type,
                    task_kind="single_call",
                    description=f"{name} under {noise_type} with {intensity} injected failure(s).",
                    goals=goals,
                    fault_profile=_profile_for_policy_noise(noise_type, target_tool, intensity=intensity),
                    payload={"tool_call": call},
                    initial_state=state,
                    source="synthetic_policy",
                    intensity=intensity,
                    intensity_label=f"level_{intensity}",
                    k=intensity + 1,
                ))

    observation_templates = _observation_policy_templates()
    for noise_type in ["vague_observation", "misleading_observation"]:
        for intensity in [1, 2, 3]:
            for template in observation_templates:
                target_tool = template["search_call"]["tool_name"]
                cases.append(PolicyNoiseCase(
                    case_name=f"synthetic_policy::{template['name']}::{noise_type}::level_{intensity}",
                    noise_type=noise_type,
                    task_kind="search_then_action",
                    description=f"{template['name']} under {noise_type} with {intensity} noisy observation(s).",
                    goals=template["goals"],
                    fault_profile=_profile_for_policy_noise(
                        noise_type,
                        target_tool,
                        intensity=intensity,
                        misleading_observation=template["misleading_observation"],
                    ),
                    payload=template,
                    initial_state=template["initial_state"],
                    source="synthetic_policy",
                    intensity=intensity,
                    intensity_label=f"level_{intensity}",
                    k=intensity + 1,
                ))

    stale_templates = _stale_policy_templates()
    for intensity in [1, 2, 3]:
        for template in stale_templates:
            target_tool = template["verify_call"]["tool_name"]
            cases.append(PolicyNoiseCase(
                case_name=f"synthetic_policy::{template['name']}::stale_state::level_{intensity}",
                noise_type="stale_state",
                task_kind="stale_then_action",
                description=f"{template['name']} under stale state with {intensity} stale replay(s).",
                goals=template["goals"],
                fault_profile=_profile_for_policy_noise("stale_state", target_tool, intensity=intensity),
                payload=template,
                initial_state=template["initial_state"],
                source="synthetic_policy",
                intensity=intensity,
                intensity_label=f"level_{intensity}",
                k=intensity + 1,
            ))
    return cases


def render_policy_noise_markdown(result: PolicyNoiseResult) -> str:
    lines = [
        "# Agent-Policy Noise Robustness Report",
        "",
        "## By Strategy and Noise",
        "",
        "| Strategy | Noise | Cases | Success@1 | Pass^k | Recovery | Cost increase | State corruption |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for metric in result.group_metrics:
        lines.append(
            f"| {metric.strategy} | {metric.noise_type} | {metric.total_cases} | "
            f"{metric.success_at_1:.1%} | {metric.pass_k:.1%} | "
            f"{metric.recovery_rate:.1%} | {metric.average_cost_increase:.2f} | "
            f"{metric.state_corruption_rate:.1%} |"
        )

    lines.extend([
        "",
        "## Noise Intensity Curve",
        "",
        "| Strategy | Noise | Intensity | Cases | Success@1 | Pass^k | Recovery | Cost increase | State corruption |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ])
    for metric in result.intensity_metrics:
        lines.append(
            f"| {metric.strategy} | {metric.noise_type} | {metric.intensity_label} | {metric.total_cases} | "
            f"{metric.success_at_1:.1%} | {metric.pass_k:.1%} | "
            f"{metric.recovery_rate:.1%} | {metric.average_cost_increase:.2f} | "
            f"{metric.state_corruption_rate:.1%} |"
        )

    lines.extend(["", "## Cases", ""])
    for item in result.results:
        lines.extend([
            f"### {item.case_name} / {item.strategy}",
            "",
            f"- Noise type: {item.noise_type}",
            f"- Source: {item.source}",
            f"- Intensity: {item.intensity_label}",
            f"- Clean success: {item.clean_success}",
            f"- Success@1: {item.success_at_1}",
            f"- Pass^k: {item.pass_k_success}",
            f"- Recovery detected: {item.recovery_detected}",
            f"- Cost increase: {item.cost_increase}",
            f"- State corrupted: {item.state_corrupted}",
            f"- Clean sequence: {_sequence(item.clean_result.trace)}",
            f"- Success@1 sequence: {_sequence(item.success_at_1_result.trace)}",
            f"- Pass^k sequence: {_sequence(item.pass_k_result.trace)}",
            "",
        ])
    return "\n".join(lines)


def _run_policy(
    case: PolicyNoiseCase,
    strategy: str,
    *,
    fault_profile: FaultProfile | None,
    allow_recovery: bool,
) -> ExperimentResult:
    state = TraceState.from_dict(case.initial_state.to_dict())
    backend = MockBackend()
    tracer = TraceRecorder()
    executor = StatefulExecutor(
        create_default_tool_registry(),
        tracer=tracer,
        config=ExecutorConfig(fault_profile=fault_profile),
        backend=backend,
    )
    environment = ToolEnvironment(state=state, backend=backend)

    for _ in range(8):
        trace = tracer.get_records()
        call = _next_call(case, strategy, trace, allow_recovery)
        if call is None:
            break
        executor.execute(call["tool_name"], state, call.get("args", {}), environment=environment)

    trace = tracer.get_records()
    return ExperimentResult(
        final_state=state,
        trace=trace,
        call_metrics=CallLevelEvaluator().evaluate(trace),
        state_metrics=StateLevelEvaluator().evaluate(state, case.goals),
        all_calls_succeeded=all(record.success for record in trace),
        final_state_hash=state.compute_hash(),
    )


def _next_call(
    case: PolicyNoiseCase,
    strategy: str,
    trace: list[ExecutionRecord],
    allow_recovery: bool,
) -> dict[str, Any] | None:
    if case.task_kind == "write_file":
        return _next_write_file(case, strategy, trace, allow_recovery)
    if case.task_kind == "single_call":
        return _next_single_call(case, strategy, trace, allow_recovery)
    if case.task_kind == "search_then_action":
        return _next_search_then_action(case, strategy, trace, allow_recovery)
    if case.task_kind == "stale_then_action":
        return _next_stale_then_action(case, strategy, trace, allow_recovery)
    if case.task_kind == "oracle_replay":
        return _next_oracle_replay(case, strategy, trace, allow_recovery)
    if case.task_kind == "vague_contact_update":
        return _next_vague_contact_update(case, strategy, trace, allow_recovery)
    if case.task_kind == "stale_contact_message":
        return _next_stale_contact_message(case, strategy, trace, allow_recovery)
    return None


def _next_single_call(
    case: PolicyNoiseCase,
    strategy: str,
    trace: list[ExecutionRecord],
    allow_recovery: bool,
) -> dict[str, Any] | None:
    call = case.payload["tool_call"]
    if not trace:
        return call
    if trace[-1].success:
        return None
    if allow_recovery and strategy in {"cot", "react", "self_refine"} and len(trace) < case.k:
        return call
    return None


def _next_search_then_action(
    case: PolicyNoiseCase,
    strategy: str,
    trace: list[ExecutionRecord],
    allow_recovery: bool,
) -> dict[str, Any] | None:
    search_call = case.payload["search_call"]
    action_call = case.payload["action_call"]
    if not trace:
        return search_call
    if any(_same_call(record, action_call) for record in trace):
        return None

    last = trace[-1]
    if last.tool_name == search_call["tool_name"]:
        if _observation_matches_payload(last, case.payload):
            return action_call
        if not allow_recovery:
            return None
        if strategy == "react" and _count_tool(trace, search_call["tool_name"]) < case.k:
            return search_call
        if strategy in {"cot", "self_refine"}:
            return action_call
    return None


def _next_stale_then_action(
    case: PolicyNoiseCase,
    strategy: str,
    trace: list[ExecutionRecord],
    allow_recovery: bool,
) -> dict[str, Any] | None:
    warmup_calls = case.payload.get("warmup_calls", [])
    mutation_calls = case.payload.get("mutation_calls", [])
    verify_call = case.payload["verify_call"]
    final_tool = case.payload.get("final_tool", "send_message_with_phone_number")

    if len(trace) < len(warmup_calls):
        return warmup_calls[len(trace)]

    mutation_start = len(warmup_calls)
    mutation_end = mutation_start + len(mutation_calls)
    if len(trace) < mutation_end:
        return mutation_calls[len(trace) - mutation_start]

    if any(record.tool_name == final_tool for record in trace):
        return None

    verify_records = [record for record in trace[mutation_end:] if record.tool_name == verify_call["tool_name"]]
    if not verify_records:
        return verify_call

    observed_value = _observed_path(verify_records[-1], case.payload["observed_path"])
    expected_value = case.payload["expected_value"]
    if observed_value != expected_value and allow_recovery and strategy in {"react", "self_refine"} and len(verify_records) < case.k:
        return verify_call

    if observed_value is None:
        if allow_recovery and strategy == "self_refine":
            observed_value = expected_value
        else:
            return None

    return {
        "tool_name": final_tool,
        "args": {
            "recipient_phone_number": case.payload.get("recipient_phone_number", "+999"),
            "content": case.payload["content_template"].format(value=observed_value),
        },
    }


def _next_oracle_replay(
    case: PolicyNoiseCase,
    strategy: str,
    trace: list[ExecutionRecord],
    allow_recovery: bool,
) -> dict[str, Any] | None:
    oracle_calls = case.payload["oracle_tool_calls"]
    if not trace:
        return oracle_calls[0]

    last = trace[-1]
    if not last.success:
        if allow_recovery and strategy in {"cot", "react", "self_refine"} and _count_tool(trace, last.tool_name) < case.k:
            return {"tool_name": last.tool_name, "args": dict(last.args)}
        return None

    target_tool = case.payload.get("target_tool")
    if last.tool_name == target_tool and not _observation_is_informative(last):
        if not allow_recovery:
            return None
        if strategy == "react" and _count_tool(trace, target_tool) < case.k:
            return {"tool_name": target_tool, "args": dict(last.args)}
        if strategy not in {"cot", "self_refine"}:
            return None

    completed_oracle_steps = sum(
        1 for record in trace
        if any(record.tool_name == call["tool_name"] and record.args == call.get("args", {}) for call in oracle_calls)
    )
    if completed_oracle_steps >= len(oracle_calls):
        return None
    return oracle_calls[completed_oracle_steps]


def _next_write_file(
    case: PolicyNoiseCase,
    strategy: str,
    trace: list[ExecutionRecord],
    allow_recovery: bool,
) -> dict[str, Any] | None:
    call = {"tool_name": "file.write", "args": {"file_id": case.payload["file_id"], "content": case.payload["content"]}}
    if not trace:
        return call
    if trace[-1].success:
        return None
    if allow_recovery and strategy in {"cot", "react", "self_refine"} and len(trace) < case.k:
        return call
    return None


def _next_vague_contact_update(
    case: PolicyNoiseCase,
    strategy: str,
    trace: list[ExecutionRecord],
    allow_recovery: bool,
) -> dict[str, Any] | None:
    search = {"tool_name": "search_contacts", "args": {"name": case.payload["name"]}}
    modify = {"tool_name": "modify_contact", "args": {"person_id": "ada", "name": case.payload["name"], "phone_number": case.payload["phone_number"]}}
    if not trace:
        return search
    if any(record.tool_name == "modify_contact" for record in trace):
        return None
    last = trace[-1]
    if last.tool_name != "search_contacts":
        return None
    if _has_hits(last):
        return modify
    if not allow_recovery:
        return None
    if strategy == "cot":
        return modify
    if strategy == "react" and _count_tool(trace, "search_contacts") < 2:
        return search
    if strategy == "self_refine":
        return modify
    return None


def _next_stale_contact_message(
    case: PolicyNoiseCase,
    strategy: str,
    trace: list[ExecutionRecord],
    allow_recovery: bool,
) -> dict[str, Any] | None:
    search = {"tool_name": "search_contacts", "args": {"name": case.payload["name"]}}
    modify = {"tool_name": "modify_contact", "args": {"person_id": "ada", "name": case.payload["name"], "phone_number": case.payload["phone_number"]}}
    if not trace:
        return search
    if not any(record.tool_name == "modify_contact" for record in trace):
        return modify if _has_hits(trace[-1]) else None
    searches_after_modify = _searches_after_last(trace, "modify_contact")
    if not searches_after_modify:
        return search
    latest_search = searches_after_modify[-1]
    observed_phone = _first_hit_field(latest_search, "phone_number")
    expected_phone = case.payload["phone_number"]
    if observed_phone != expected_phone and allow_recovery and strategy in {"react", "self_refine"} and len(searches_after_modify) < 2:
        return search
    if any(record.tool_name == "send_message_with_phone_number" for record in trace):
        return None
    phone_for_message = observed_phone or expected_phone
    return {
        "tool_name": "send_message_with_phone_number",
        "args": {
            "recipient_phone_number": case.payload["recipient_phone_number"],
            "content": f"{case.payload['name']} phone is {phone_for_message}",
        },
    }


def _compute_group_metrics(
    results: list[PolicyNoiseRunResult],
    strategies: list[str],
) -> list[PolicyNoiseGroupMetrics]:
    noise_types = sorted({result.noise_type for result in results})
    metrics: list[PolicyNoiseGroupMetrics] = []
    for strategy in strategies:
        for noise_type in noise_types:
            group = [result for result in results if result.strategy == strategy and result.noise_type == noise_type]
            total = len(group)
            recovery_opportunities = sum(1 for result in group if not result.success_at_1)
            metrics.append(PolicyNoiseGroupMetrics(
                strategy=strategy,
                noise_type=noise_type,
                total_cases=total,
                success_at_1=_rate(sum(1 for result in group if result.success_at_1), total),
                pass_k=_rate(sum(1 for result in group if result.pass_k_success), total),
                recovery_rate=_rate(sum(1 for result in group if result.recovery_detected), recovery_opportunities),
                average_cost_increase=_rate(sum(result.cost_increase for result in group), total),
                state_corruption_rate=_rate(sum(1 for result in group if result.state_corrupted), total),
            ))
    return metrics


def _compute_intensity_metrics(
    results: list[PolicyNoiseRunResult],
    strategies: list[str],
) -> list[PolicyNoiseGroupMetrics]:
    metrics: list[PolicyNoiseGroupMetrics] = []
    noise_types = sorted({result.noise_type for result in results})
    intensity_labels = sorted({result.intensity_label for result in results})
    for strategy in strategies:
        for noise_type in noise_types:
            for intensity_label in intensity_labels:
                group = [
                    result for result in results
                    if result.strategy == strategy
                    and result.noise_type == noise_type
                    and result.intensity_label == intensity_label
                ]
                if not group:
                    continue
                total = len(group)
                recovery_opportunities = sum(1 for result in group if not result.success_at_1)
                metrics.append(PolicyNoiseGroupMetrics(
                    strategy=strategy,
                    noise_type=noise_type,
                    intensity_label=intensity_label,
                    total_cases=total,
                    success_at_1=_rate(sum(1 for result in group if result.success_at_1), total),
                    pass_k=_rate(sum(1 for result in group if result.pass_k_success), total),
                    recovery_rate=_rate(sum(1 for result in group if result.recovery_detected), recovery_opportunities),
                    average_cost_increase=_rate(sum(result.cost_increase for result in group), total),
                    state_corruption_rate=_rate(sum(1 for result in group if result.state_corrupted), total),
                ))
    return metrics


def _goals_passed(result: ExperimentResult) -> bool:
    return result.state_metrics is not None and result.state_metrics.all_passed


def _has_hits(record: ExecutionRecord) -> bool:
    hits = record.observation.get("hits")
    return isinstance(hits, list) and len(hits) > 0


def _first_hit_field(record: ExecutionRecord, field: str) -> Any:
    hits = record.observation.get("hits")
    if not isinstance(hits, list) or not hits:
        return None
    return hits[0].get(field)


def _searches_after_last(trace: list[ExecutionRecord], tool_name: str) -> list[ExecutionRecord]:
    last_index = max((idx for idx, record in enumerate(trace) if record.tool_name == tool_name), default=-1)
    return [record for record in trace[last_index + 1:] if record.tool_name == "search_contacts"]


def _count_tool(trace: list[ExecutionRecord], tool_name: str) -> int:
    return sum(1 for record in trace if record.tool_name == tool_name)


def _sequence(trace: list[ExecutionRecord]) -> str:
    return " -> ".join(record.tool_name for record in trace)


def _rate(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def _profile_for_policy_noise(
    noise_type: str,
    target_tool: str,
    *,
    intensity: int,
    misleading_observation: dict[str, Any] | None = None,
) -> FaultProfile:
    if noise_type == "timeout":
        return FaultProfile(
            timeout_failures={target_tool: intensity},
            latency_ms_by_tool={target_tool: 5},
        )
    if noise_type == "schema_drift":
        return FaultProfile(schema_drift_failures={target_tool: intensity})
    if noise_type == "stale_state":
        return FaultProfile(stale_observation_replays={target_tool: intensity})
    if noise_type == "vague_observation":
        return FaultProfile(vague_observation_failures={target_tool: intensity})
    if noise_type == "misleading_observation":
        return FaultProfile(
            misleading_observations_by_tool={target_tool: misleading_observation or {"hits": [], "count": 0}},
            misleading_observation_failures={target_tool: intensity},
        )
    return FaultProfile()


def _select_toolsandbox_policy_subset(cases: list[Any], *, per_domain: int) -> list[Any]:
    grouped: dict[str, list[Any]] = {}
    for case in cases:
        grouped.setdefault(case.domain or "unknown", []).append(case)

    selected: list[Any] = []
    seen_names: set[str] = set()
    for domain in sorted(grouped):
        for case in _diverse_toolsandbox_policy_cases(grouped[domain], per_domain):
            if case.scenario_name in seen_names:
                continue
            selected.append(case)
            seen_names.add(case.scenario_name)
    return selected


def _diverse_toolsandbox_policy_cases(cases: list[Any], limit: int) -> list[Any]:
    ordered = sorted(cases, key=lambda case: (
        str(case.metadata.get("canonical_task_key") or ""),
        len(case.oracle_tool_calls),
        case.scenario_name,
    ))
    selected: list[Any] = []
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


def _default_toolsandbox_path() -> Path:
    if env_path := os.environ.get("AGENTINFERKIT_TOOLSANDBOX_PATH"):
        return Path(env_path)
    return Path(__file__).resolve().parents[3] / "Toolsandbox" / "tool_sandbox_scenarios.json"


def _first_observation_tool(tool_calls: list[dict[str, Any]]) -> str | None:
    for call in tool_calls:
        tool_name = str(call.get("tool_name", ""))
        if _is_observation_tool(tool_name):
            return tool_name
    return None


def _is_observation_tool(tool_name: str) -> bool:
    return (
        "search" in tool_name
        or tool_name.startswith("get_")
        or tool_name.endswith(".query")
        or tool_name.endswith(".read")
    )


def _observation_policy_templates() -> list[dict[str, Any]]:
    contact_state = _state_with_contact("ada", "Ada", "+000")
    reminder_state = _state_with_reminder("rem1", "pay rent", 100.0)
    message_state = _state_with_message("msg1", "invoice pending")
    setting_state = _toolsandbox_base_state()
    _set_device_fields(setting_state, wifi=False)
    calendar_state = _toolsandbox_base_state()
    calendar_state.set_entity("calendar_event", "evt1", {
        "event_id": "evt1",
        "title": "Sync",
        "start_time": 9.0,
        "end_time": 10.0,
        "participants": ["ana"],
        "location": "Room A",
        "status": "scheduled",
    })

    return [
        {
            "name": "contact_search_update",
            "search_call": {"tool_name": "search_contacts", "args": {"name": "Ada"}},
            "action_call": {"tool_name": "modify_contact", "args": {"person_id": "ada", "name": "Ada", "phone_number": "+200"}},
            "goals": [{"type": "toolsandbox_record_exists", "entity_type": "contact", "fields": {"name": "Ada", "phone_number": "+200"}}],
            "initial_state": contact_state,
            "expected_path": ["hits", 0, "name"],
            "expected_value": "Ada",
            "misleading_observation": {"hits": [{"name": "Bob", "phone_number": "+404"}], "count": 1},
        },
        {
            "name": "reminder_search_update",
            "search_call": {"tool_name": "search_reminder", "args": {"content": "pay"}},
            "action_call": {"tool_name": "modify_reminder", "args": {"reminder_id": "rem1", "content": "pay rent", "reminder_timestamp": 200.0}},
            "goals": [{"type": "toolsandbox_record_exists", "entity_type": "reminder", "fields": {"content": "pay rent", "reminder_timestamp": 200.0}}],
            "initial_state": reminder_state,
            "expected_path": ["hits", 0, "content"],
            "expected_value": "pay rent",
            "misleading_observation": {"hits": [{"content": "cancel gym"}], "count": 1},
        },
        {
            "name": "message_search_send",
            "search_call": {"tool_name": "search_messages", "args": {"content": "invoice"}},
            "action_call": {"tool_name": "send_message_with_phone_number", "args": {"recipient_phone_number": "+555", "content": "invoice received"}},
            "goals": [{"type": "toolsandbox_record_exists", "entity_type": "messaging", "fields": {"recipient_phone_number": "+555", "content": "invoice received"}}],
            "initial_state": message_state,
            "expected_path": ["hits", 0, "content"],
            "expected_value": "invoice pending",
            "misleading_observation": {"hits": [{"content": "dinner plan"}], "count": 1},
        },
        {
            "name": "setting_get_then_set",
            "search_call": {"tool_name": "get_wifi_status", "args": {}},
            "action_call": {"tool_name": "set_wifi_status", "args": {"wifi": True}},
            "goals": [{"type": "toolsandbox_setting_equals", "field": "wifi", "expected": True}],
            "initial_state": setting_state,
            "expected_path": ["wifi"],
            "expected_value": False,
            "misleading_observation": {"wifi": True},
        },
        {
            "name": "calendar_search_update",
            "search_call": {"tool_name": "calendar.search_events", "args": {"participant": "ana"}},
            "action_call": {"tool_name": "calendar.update_event", "args": {"event_id": "evt1", "location": "Room B"}},
            "goals": [{"type": "event_field_equals", "event_id": "evt1", "field": "location", "expected": "Room B"}],
            "initial_state": calendar_state,
            "expected_path": ["hits", 0, "event_id"],
            "expected_value": "evt1",
            "misleading_observation": {"hits": [{"event_id": "evt404", "location": "Nowhere"}], "count": 1},
        },
    ]


def _stale_policy_templates() -> list[dict[str, Any]]:
    contact_state = _state_with_contact("ada", "Ada", "+000")
    reminder_state = _state_with_reminder("rem1", "pay rent", 100.0)
    calendar_state = _toolsandbox_base_state()
    calendar_state.set_entity("calendar_event", "evt1", {
        "event_id": "evt1",
        "title": "Sync",
        "start_time": 9.0,
        "end_time": 10.0,
        "participants": ["ana"],
        "location": "Room A",
        "status": "scheduled",
    })
    file_state = _toolsandbox_base_state()
    setting_state = _toolsandbox_base_state()
    _set_device_fields(setting_state, wifi=False)

    return [
        {
            "name": "contact_stale_message",
            "warmup_calls": [{"tool_name": "search_contacts", "args": {"name": "Ada"}}],
            "mutation_calls": [{"tool_name": "modify_contact", "args": {"person_id": "ada", "name": "Ada", "phone_number": "+200"}}],
            "verify_call": {"tool_name": "search_contacts", "args": {"name": "Ada"}},
            "observed_path": ["hits", 0, "phone_number"],
            "expected_value": "+200",
            "content_template": "Ada phone is {value}",
            "goals": [{"type": "toolsandbox_record_exists", "entity_type": "messaging", "fields": {"recipient_phone_number": "+999", "content": "Ada phone is +200"}}],
            "initial_state": contact_state,
        },
        {
            "name": "reminder_stale_message",
            "warmup_calls": [{"tool_name": "search_reminder", "args": {"content": "pay"}}],
            "mutation_calls": [{"tool_name": "modify_reminder", "args": {"reminder_id": "rem1", "content": "pay rent", "reminder_timestamp": 200.0}}],
            "verify_call": {"tool_name": "search_reminder", "args": {"content": "pay"}},
            "observed_path": ["hits", 0, "reminder_timestamp"],
            "expected_value": 200.0,
            "content_template": "Reminder timestamp is {value}",
            "goals": [{"type": "toolsandbox_record_exists", "entity_type": "messaging", "fields": {"recipient_phone_number": "+999", "content": "Reminder timestamp is 200.0"}}],
            "initial_state": reminder_state,
        },
        {
            "name": "calendar_stale_message",
            "warmup_calls": [{"tool_name": "calendar.search_events", "args": {"participant": "ana"}}],
            "mutation_calls": [{"tool_name": "calendar.update_event", "args": {"event_id": "evt1", "location": "Room B"}}],
            "verify_call": {"tool_name": "calendar.search_events", "args": {"participant": "ana"}},
            "observed_path": ["hits", 0, "location"],
            "expected_value": "Room B",
            "content_template": "Calendar location is {value}",
            "goals": [{"type": "toolsandbox_record_exists", "entity_type": "messaging", "fields": {"recipient_phone_number": "+999", "content": "Calendar location is Room B"}}],
            "initial_state": calendar_state,
        },
        {
            "name": "file_index_stale_message",
            "warmup_calls": [
                {"tool_name": "file.write", "args": {"file_id": "stale_file", "content": "old alpha"}},
                {"tool_name": "search.index", "args": {"file_id": "stale_file"}},
                {"tool_name": "search.query", "args": {"query": "alpha"}},
            ],
            "mutation_calls": [
                {"tool_name": "file.write", "args": {"file_id": "stale_file", "content": "new alpha"}},
                {"tool_name": "search.index", "args": {"file_id": "stale_file"}},
            ],
            "verify_call": {"tool_name": "search.query", "args": {"query": "alpha"}},
            "observed_path": ["hits", 0, "content"],
            "expected_value": "new alpha",
            "content_template": "Indexed file says {value}",
            "goals": [{"type": "toolsandbox_record_exists", "entity_type": "messaging", "fields": {"recipient_phone_number": "+999", "content": "Indexed file says new alpha"}}],
            "initial_state": file_state,
        },
        {
            "name": "setting_stale_message",
            "warmup_calls": [{"tool_name": "get_wifi_status", "args": {}}],
            "mutation_calls": [{"tool_name": "set_wifi_status", "args": {"wifi": True}}],
            "verify_call": {"tool_name": "get_wifi_status", "args": {}},
            "observed_path": ["wifi"],
            "expected_value": True,
            "content_template": "WiFi status is {value}",
            "goals": [{"type": "toolsandbox_record_exists", "entity_type": "messaging", "fields": {"recipient_phone_number": "+999", "content": "WiFi status is True"}}],
            "initial_state": setting_state,
        },
    ]


def _state_with_contact(person_id: str, name: str, phone_number: str) -> TraceState:
    state = _toolsandbox_base_state()
    state.set_entity("contact", person_id, {
        "person_id": person_id,
        "name": name,
        "phone_number": phone_number,
        "relationship": "coworker",
        "is_self": False,
    })
    return state


def _state_with_reminder(reminder_id: str, content: str, timestamp: float) -> TraceState:
    state = _toolsandbox_base_state()
    state.set_entity("reminder", reminder_id, {
        "reminder_id": reminder_id,
        "content": content,
        "reminder_timestamp": timestamp,
    })
    return state


def _state_with_message(message_id: str, content: str) -> TraceState:
    state = _toolsandbox_base_state()
    state.set_entity("messaging", message_id, {
        "message_id": message_id,
        "content": content,
        "recipient_phone_number": "+100",
    })
    return state


def _toolsandbox_base_state() -> TraceState:
    state = TraceState()
    ensure_toolsandbox_state(state)
    state.set_entity("contact", "self", {
        "person_id": "self",
        "name": "Self",
        "phone_number": "+10000000000",
        "relationship": None,
        "is_self": True,
    })
    return state


def _set_device_fields(state: TraceState, **fields: Any) -> None:
    device = dict(state.get_entity("setting", "device") or {})
    device.update(fields)
    state.set_entity("setting", "device", device)


def _observation_matches_payload(record: ExecutionRecord, payload: dict[str, Any]) -> bool:
    return _observed_path(record, payload["expected_path"]) == payload["expected_value"]


def _observed_path(record: ExecutionRecord, path: list[Any]) -> Any:
    value: Any = record.observation
    for part in path:
        if isinstance(part, int):
            if not isinstance(value, list) or len(value) <= part:
                return None
            value = value[part]
        else:
            if not isinstance(value, dict):
                return None
            value = value.get(part)
    return value


def _observation_is_informative(record: ExecutionRecord) -> bool:
    if not record.success:
        return False
    if "fault" not in record.metadata:
        return True
    return record.metadata.get("fault") not in {"vague_observation", "misleading_observation", "stale_observation"}


def _same_call(record: ExecutionRecord, call: dict[str, Any]) -> bool:
    return record.tool_name == call.get("tool_name") and record.args == call.get("args", {})
