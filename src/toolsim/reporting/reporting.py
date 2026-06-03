"""Comparison experiment result aggregation and export module."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from toolsim.runners.comparison_runner import ComparisonCase, ComparisonResult, ComparisonRunner
from toolsim.evaluators.overview_summary import OverviewMetrics, compute_overview_metrics, generate_overall_conclusion
from toolsim.evaluators.trajectory_evaluator import summarize_trajectory_difference
from toolsim.core.utils import extract_last_query_hits


@dataclass
class CaseComparisonSummary:
    case_name: str
    description: str
    stateful_outcome: str
    stateless_outcome: str
    key_difference: str
    key_process_difference: str
    stateful_goals_passed: bool | None
    stateless_goals_passed: bool | None
    stateful_all_calls_succeeded: bool
    stateless_all_calls_succeeded: bool
    stateful_trace_length: int
    stateless_trace_length: int
    stateful_tool_sequence: str
    stateless_tool_sequence: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_name": self.case_name,
            "description": self.description,
            "stateful_outcome": self.stateful_outcome,
            "stateless_outcome": self.stateless_outcome,
            "key_difference": self.key_difference,
            "key_process_difference": self.key_process_difference,
            "stateful_goals_passed": self.stateful_goals_passed,
            "stateless_goals_passed": self.stateless_goals_passed,
            "stateful_all_calls_succeeded": self.stateful_all_calls_succeeded,
            "stateless_all_calls_succeeded": self.stateless_all_calls_succeeded,
            "stateful_trace_length": self.stateful_trace_length,
            "stateless_trace_length": self.stateless_trace_length,
            "stateful_tool_sequence": self.stateful_tool_sequence,
            "stateless_tool_sequence": self.stateless_tool_sequence,
        }


@dataclass
class BatchComparisonResult:
    results: list[ComparisonResult]
    summaries: list[CaseComparisonSummary]
    total_cases: int
    stateful_goal_pass_count: int
    stateless_goal_pass_count: int
    stateful_all_calls_succeeded_count: int
    stateless_all_calls_succeeded_count: int
    overview_metrics: OverviewMetrics
    overall_conclusion: str
    case_names: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_cases": self.total_cases,
            "stateful_goal_pass_count": self.stateful_goal_pass_count,
            "stateless_goal_pass_count": self.stateless_goal_pass_count,
            "stateful_all_calls_succeeded_count": self.stateful_all_calls_succeeded_count,
            "stateless_all_calls_succeeded_count": self.stateless_all_calls_succeeded_count,
            "overview_metrics": self.overview_metrics.to_dict(),
            "overall_conclusion": self.overall_conclusion,
            "case_names": self.case_names,
            "results": [result.to_dict() for result in self.results],
            "summaries": [summary.to_dict() for summary in self.summaries],
        }


class BatchComparisonRunner:
    """Run multiple comparison cases sequentially and produce aggregate batch results."""

    def __init__(self, comparison_runner: ComparisonRunner | None = None) -> None:
        self._comparison_runner = comparison_runner or ComparisonRunner()

    def run(self, cases: list[ComparisonCase]) -> BatchComparisonResult:
        results: list[ComparisonResult] = []
        summaries: list[CaseComparisonSummary] = []

        for case in cases:
            result = self._comparison_runner.run_case(case)
            results.append(result)
            summaries.append(summarize_comparison_result(case, result))

        overview_metrics = compute_overview_metrics(results)
        overall_conclusion = generate_overall_conclusion(overview_metrics)

        return BatchComparisonResult(
            results=results,
            summaries=summaries,
            total_cases=len(results),
            stateful_goal_pass_count=sum(1 for s in summaries if s.stateful_goals_passed is True),
            stateless_goal_pass_count=sum(1 for s in summaries if s.stateless_goals_passed is True),
            stateful_all_calls_succeeded_count=sum(1 for s in summaries if s.stateful_all_calls_succeeded),
            stateless_all_calls_succeeded_count=sum(1 for s in summaries if s.stateless_all_calls_succeeded),
            overview_metrics=overview_metrics,
            overall_conclusion=overall_conclusion,
            case_names=[case.case_name for case in cases],
        )


def summarize_comparison_result(case: ComparisonCase, result: ComparisonResult) -> CaseComparisonSummary:
    """Summarise a single comparison case result into a human-readable structure."""
    stateful_hits = extract_last_query_hits(result.stateful_result.trace)
    stateless_hits = extract_last_query_hits(result.stateless_result.trace)
    trajectory_summary = summarize_trajectory_difference(result)

    stateful_outcome = _build_outcome_text(
        label="Stateful",
        hits=stateful_hits,
        trace_length=len(result.stateful_result.trace),
        goals_passed=result.summary.get("stateful_all_goals_passed"),
        final_state=result.stateful_result.final_state,
    )
    stateless_outcome = _build_outcome_text(
        label="Stateless",
        hits=stateless_hits,
        trace_length=len(result.stateless_result.trace),
        goals_passed=result.summary.get("stateless_all_goals_passed"),
        final_state=result.stateless_result.final_state,
    )

    return CaseComparisonSummary(
        case_name=case.case_name,
        description=case.description,
        stateful_outcome=stateful_outcome,
        stateless_outcome=stateless_outcome,
        key_difference=_build_key_difference(case, result, stateful_hits, stateless_hits),
        key_process_difference=trajectory_summary.key_process_difference,
        stateful_goals_passed=result.summary.get("stateful_all_goals_passed"),
        stateless_goals_passed=result.summary.get("stateless_all_goals_passed"),
        stateful_all_calls_succeeded=result.summary.get("stateful_all_calls_succeeded", False),
        stateless_all_calls_succeeded=result.summary.get("stateless_all_calls_succeeded", False),
        stateful_trace_length=trajectory_summary.stateful_total_steps,
        stateless_trace_length=trajectory_summary.stateless_total_steps,
        stateful_tool_sequence=" -> ".join(trajectory_summary.stateful_tool_sequence),
        stateless_tool_sequence=" -> ".join(trajectory_summary.stateless_tool_sequence),
    )


def render_markdown_report(batch_result: BatchComparisonResult) -> str:
    """Render a batch comparison result as a Markdown report string."""
    metrics = batch_result.overview_metrics
    lines = [
        "# Stateless vs Stateful Comparison Report",
        "",
        "## Overview",
        f"- Total cases: {batch_result.total_cases}",
        f"- Stateful passed cases: {batch_result.stateful_goal_pass_count}",
        f"- Stateless passed cases: {batch_result.stateless_goal_pass_count}",
        f"- Stateful all-calls-succeeded count: {batch_result.stateful_all_calls_succeeded_count}",
        f"- Stateless all-calls-succeeded count: {batch_result.stateless_all_calls_succeeded_count}",
        "",
        "## Overview Metrics",
        f"- Stateful success rate: {metrics.stateful_success_rate:.2%}",
        f"- Stateless success rate: {metrics.stateless_success_rate:.2%}",
        f"- Stateful invalid call rate: {metrics.stateful_invalid_call_rate:.2%}",
        f"- Stateless invalid call rate: {metrics.stateless_invalid_call_rate:.2%}",
        f"- Stateful recovery rate: {metrics.stateful_recovery_rate:.2%}",
        f"- Stateless recovery rate: {metrics.stateless_recovery_rate:.2%}",
        f"- Stateful average steps: {metrics.stateful_avg_steps:.2f}",
        f"- Stateless average steps: {metrics.stateless_avg_steps:.2f}",
        f"- Stateful final state correctness: {metrics.stateful_final_state_correctness:.2%}",
        f"- Stateless final state correctness: {metrics.stateless_final_state_correctness:.2%}",
        f"- Cases with step count difference: {metrics.cases_with_step_count_difference}",
        f"- Cases with explicit dependency resolution: {metrics.cases_with_explicit_dependency_resolution}",
        f"- Cases with query before index: {metrics.cases_with_query_before_index}",
        f"- Cases with overwrite without re-index: {metrics.cases_with_overwrite_without_reindex}",
        f"- Cases with trajectory divergence: {metrics.cases_with_trajectory_divergence}",
        f"- Cases with snapshot semantics difference: {metrics.cases_with_snapshot_semantics_difference}",
        f"- Cases with retrieval outcome difference: {metrics.cases_with_retrieval_outcome_difference}",
        "",
        "## Overall Conclusion",
        batch_result.overall_conclusion,
        "",
    ]

    for summary in batch_result.summaries:
        lines.extend([
            f"## {summary.case_name}",
            "",
            f"- Description: {summary.description}",
            f"- Stateful outcome: {summary.stateful_outcome}",
            f"- Stateless outcome: {summary.stateless_outcome}",
            f"- Stateful steps: {summary.stateful_trace_length}",
            f"- Stateless steps: {summary.stateless_trace_length}",
            f"- Stateful sequence: {summary.stateful_tool_sequence}",
            f"- Stateless sequence: {summary.stateless_tool_sequence}",
            f"- Key difference: {summary.key_difference}",
            f"- Key process difference: {summary.key_process_difference}",
            "",
        ])

    return "\n".join(lines)


def _build_outcome_text(
    label: str,
    hits: list[dict[str, Any]],
    trace_length: int,
    goals_passed: bool | None,
    final_state: Any | None = None,
) -> str:
    if hits:
        file_ids = ", ".join(hit.get("file_id", "?") for hit in hits)
        return (
            f"{label} completed {trace_length} calls and returned {len(hits)} hit(s) "
            f"for file(s): {file_ids}. Goals passed: {goals_passed}."
        )
    if final_state is not None:
        issues = final_state.entities.get("issue", {})
        if issues:
            issue_states = ", ".join(
                f"{issue_id}={issue.get('status', '?')}"
                for issue_id, issue in sorted(issues.items())
            )
            return (
                f"{label} completed {trace_length} calls and final issue state(s): "
                f"{issue_states}. Goals passed: {goals_passed}."
            )
        events = final_state.entities.get("calendar_event", {})
        if events:
            event_states = ", ".join(
                f"{event_id}={event.get('status', '?')}@{event.get('start_time', '?')}"
                for event_id, event in sorted(events.items())
            )
            return (
                f"{label} completed {trace_length} calls and final event state(s): "
                f"{event_states}. Goals passed: {goals_passed}."
            )
    return (
        f"{label} completed {trace_length} calls and returned no final query hits. "
        f"Goals passed: {goals_passed}."
    )


def _build_key_difference(
    case: ComparisonCase,
    result: ComparisonResult,
    stateful_hits: list[dict[str, Any]],
    stateless_hits: list[dict[str, Any]],
) -> str:
    stateful_trace_tools = [record.tool_name for record in result.stateful_result.trace]
    current_file = result.stateful_result.final_state.get_entity("file", "f1")
    current_content = current_file.get("content") if current_file is not None else None

    if not stateful_hits and stateless_hits:
        return (
            "Stateful query missed because the file was not indexed, while stateless query directly "
            "searched current file content."
        )

    if stateful_hits and stateless_hits and "search.index" in stateful_trace_tools:
        stateful_hit_ids = {hit.get("file_id") for hit in stateful_hits}
        stateless_hit_ids = {hit.get("file_id") for hit in stateless_hits}
        if stateful_hit_ids != stateless_hit_ids:
            return (
                "Stateful search returned only explicitly indexed file snapshots, while stateless search "
                "scanned all current file content."
            )
        return "Stateful system required explicit indexing before retrieval, while stateless query did not."

    if stateful_hits and not stateless_hits:
        first_stateful_content = stateful_hits[0].get("content")
        if current_content is not None and first_stateful_content != current_content:
            return (
                "Stateful search used indexed snapshot and did not reflect overwritten content before re-index, "
                "while stateless query reflected the latest file content."
            )

    stateful_tools = [record.tool_name for record in result.stateful_result.trace]
    stateless_tools = [record.tool_name for record in result.stateless_result.trace]
    if "issue.close" in stateful_tools and "issue.close" in stateless_tools:
        stateful_failed_close = any(record.tool_name == "issue.close" and not record.success for record in result.stateful_result.trace)
        if stateful_failed_close:
            return (
                "Stateful issue workflow rejected close-before-assignment and required recovery, "
                "while the stateless baseline accepted the direct close."
            )

    if "issue.reopen" in stateful_tools and "issue.reopen" in stateless_tools:
        stateful_failed_reopen = any(record.tool_name == "issue.reopen" and not record.success for record in result.stateful_result.trace)
        if stateful_failed_reopen:
            return (
                "Stateful issue workflow rejected reopen-before-close and required a close-then-reopen recovery, "
                "while the stateless baseline accepted reopening directly."
            )

    stateful_failed_calendar_conflict = any(
        record.tool_name in {"calendar.create_event", "calendar.update_event"}
        and not record.success
        and "Conflict detected" in (record.error or "")
        for record in result.stateful_result.trace
    )
    if stateful_failed_calendar_conflict:
        return (
            "Stateful calendar workflow rejected a participant conflict and required a non-conflicting retry, "
            "while the stateless baseline accepted the conflicting mutation."
        )

    if case.case_name.startswith("toolsandbox::"):
        if stateful_tools != stateless_tools:
            return (
                "Stateful ToolSandbox execution preserved helper/search/tool-trace milestones, while the "
                "stateless baseline collapsed the task to final-state mutations and final user-visible output."
            )
        return (
            "This ToolSandbox case is already a direct final-state mutation, so stateful and stateless "
            "trajectories remain structurally similar."
        )

    return (
        f"Stateful and stateless outcomes diverged under case {case.case_name!r}; "
        "inspect trace and goals for details."
    )
