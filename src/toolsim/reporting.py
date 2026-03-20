"""
reporting.py — 最小可运行的对比实验结果汇总与导出模块
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from toolsim.comparison_runner import ComparisonCase, ComparisonResult, ComparisonRunner
from toolsim.overview_summary import OverviewMetrics, compute_overview_metrics, generate_overall_conclusion
from toolsim.trajectory_evaluator import summarize_trajectory_difference


@dataclass
class CaseComparisonSummary:
    case_name: str
    description: str
    stateful_outcome: str
    stateless_outcome: str
    key_difference: str
    key_process_difference: str
    stateful_goals_passed: Optional[bool]
    stateless_goals_passed: Optional[bool]
    stateful_all_calls_succeeded: bool
    stateless_all_calls_succeeded: bool
    stateful_trace_length: int
    stateless_trace_length: int
    stateful_tool_sequence: str
    stateless_tool_sequence: str

    def to_dict(self) -> Dict[str, Any]:
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
    results: List[ComparisonResult]
    summaries: List[CaseComparisonSummary]
    total_cases: int
    stateful_goal_pass_count: int
    stateless_goal_pass_count: int
    stateful_all_calls_succeeded_count: int
    stateless_all_calls_succeeded_count: int
    overview_metrics: OverviewMetrics
    overall_conclusion: str
    case_names: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
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
    """顺序运行多个 comparison cases，并产出批量汇总结果。"""

    def __init__(self, comparison_runner: Optional[ComparisonRunner] = None) -> None:
        self._comparison_runner = comparison_runner or ComparisonRunner()

    def run(self, cases: List[ComparisonCase]) -> BatchComparisonResult:
        results: List[ComparisonResult] = []
        summaries: List[CaseComparisonSummary] = []

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
            stateful_goal_pass_count=sum(1 for summary in summaries if summary.stateful_goals_passed is True),
            stateless_goal_pass_count=sum(1 for summary in summaries if summary.stateless_goals_passed is True),
            stateful_all_calls_succeeded_count=sum(1 for summary in summaries if summary.stateful_all_calls_succeeded),
            stateless_all_calls_succeeded_count=sum(1 for summary in summaries if summary.stateless_all_calls_succeeded),
            overview_metrics=overview_metrics,
            overall_conclusion=overall_conclusion,
            case_names=[case.case_name for case in cases],
        )


def summarize_comparison_result(case: ComparisonCase, result: ComparisonResult) -> CaseComparisonSummary:
    stateful_hits = _extract_last_query_hits(result.stateful_result)
    stateless_hits = _extract_last_query_hits(result.stateless_result)
    trajectory_summary = summarize_trajectory_difference(result)

    stateful_outcome = _build_outcome_text(
        label="Stateful",
        hits=stateful_hits,
        trace_length=len(result.stateful_result.trace),
        goals_passed=result.summary.get("stateful_all_goals_passed"),
    )
    stateless_outcome = _build_outcome_text(
        label="Stateless",
        hits=stateless_hits,
        trace_length=len(result.stateless_result.trace),
        goals_passed=result.summary.get("stateless_all_goals_passed"),
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
        f"- Stateful average steps: {metrics.stateful_avg_steps:.2f}",
        f"- Stateless average steps: {metrics.stateless_avg_steps:.2f}",
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
        lines.extend(
            [
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
            ]
        )

    return "\n".join(lines)


def _build_outcome_text(
    label: str,
    hits: List[Dict[str, Any]],
    trace_length: int,
    goals_passed: Optional[bool],
) -> str:
    if hits:
        file_ids = ", ".join(hit.get("file_id", "?") for hit in hits)
        return (
            f"{label} completed {trace_length} calls and returned {len(hits)} hit(s) "
            f"for file(s): {file_ids}. Goals passed: {goals_passed}."
        )
    return (
        f"{label} completed {trace_length} calls and returned no final query hits. "
        f"Goals passed: {goals_passed}."
    )


def _build_key_difference(
    case: ComparisonCase,
    result: ComparisonResult,
    stateful_hits: List[Dict[str, Any]],
    stateless_hits: List[Dict[str, Any]],
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
        return "Stateful system required explicit indexing before retrieval, while stateless query did not."

    if stateful_hits and not stateless_hits:
        first_stateful_content = stateful_hits[0].get("content")
        if current_content is not None and first_stateful_content != current_content:
            return (
                "Stateful search used indexed snapshot and did not reflect overwritten content before re-index, "
                "while stateless query reflected the latest file content."
            )

    return (
        f"Stateful and stateless outcomes diverged under case {case.case_name!r}; inspect trace and goals for details."
    )


def _extract_last_query_hits(experiment_result: Any) -> List[Dict[str, Any]]:
    for record in reversed(experiment_result.trace):
        if record.tool_name == "search.query":
            return record.observation.get("hits", [])
    return []
