"""
overview_summary.py — 最小可运行的 overview 聚合指标与自动结论生成模块
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Sequence

from toolsim.comparison_runner import ComparisonResult
from toolsim.trajectory_evaluator import summarize_trajectory_difference


@dataclass
class OverviewMetrics:
    total_cases: int
    stateful_goal_pass_count: int
    stateless_goal_pass_count: int
    stateful_all_calls_succeeded_count: int
    stateless_all_calls_succeeded_count: int
    stateful_total_steps_sum: int
    stateless_total_steps_sum: int
    stateful_avg_steps: float
    stateless_avg_steps: float
    cases_with_step_count_difference: int
    cases_with_explicit_dependency_resolution: int
    cases_with_query_before_index: int
    cases_with_overwrite_without_reindex: int
    cases_with_trajectory_divergence: int
    cases_with_snapshot_semantics_difference: int
    cases_with_retrieval_outcome_difference: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_cases": self.total_cases,
            "stateful_goal_pass_count": self.stateful_goal_pass_count,
            "stateless_goal_pass_count": self.stateless_goal_pass_count,
            "stateful_all_calls_succeeded_count": self.stateful_all_calls_succeeded_count,
            "stateless_all_calls_succeeded_count": self.stateless_all_calls_succeeded_count,
            "stateful_total_steps_sum": self.stateful_total_steps_sum,
            "stateless_total_steps_sum": self.stateless_total_steps_sum,
            "stateful_avg_steps": self.stateful_avg_steps,
            "stateless_avg_steps": self.stateless_avg_steps,
            "cases_with_step_count_difference": self.cases_with_step_count_difference,
            "cases_with_explicit_dependency_resolution": self.cases_with_explicit_dependency_resolution,
            "cases_with_query_before_index": self.cases_with_query_before_index,
            "cases_with_overwrite_without_reindex": self.cases_with_overwrite_without_reindex,
            "cases_with_trajectory_divergence": self.cases_with_trajectory_divergence,
            "cases_with_snapshot_semantics_difference": self.cases_with_snapshot_semantics_difference,
            "cases_with_retrieval_outcome_difference": self.cases_with_retrieval_outcome_difference,
        }


def compute_overview_metrics(results: Sequence[ComparisonResult]) -> OverviewMetrics:
    total_cases = len(results)
    stateful_total_steps_sum = 0
    stateless_total_steps_sum = 0
    cases_with_step_count_difference = 0
    cases_with_explicit_dependency_resolution = 0
    cases_with_query_before_index = 0
    cases_with_overwrite_without_reindex = 0
    cases_with_trajectory_divergence = 0
    cases_with_snapshot_semantics_difference = 0
    cases_with_retrieval_outcome_difference = 0

    for result in results:
        trajectory = summarize_trajectory_difference(result)
        stateful_total_steps_sum += trajectory.stateful_total_steps
        stateless_total_steps_sum += trajectory.stateless_total_steps

        if trajectory.stateful_total_steps != trajectory.stateless_total_steps:
            cases_with_step_count_difference += 1
        if "explicit indexing" in trajectory.key_process_difference:
            cases_with_explicit_dependency_resolution += 1
        if "queried before dependency completion" in trajectory.key_process_difference:
            cases_with_query_before_index += 1
        if "overwrite-without-reindex" in trajectory.key_process_difference:
            cases_with_overwrite_without_reindex += 1
        if trajectory.stateful_tool_sequence != trajectory.stateless_tool_sequence:
            cases_with_trajectory_divergence += 1
        if _has_snapshot_semantics_difference(result, trajectory):
            cases_with_snapshot_semantics_difference += 1
        if _has_retrieval_outcome_difference(result):
            cases_with_retrieval_outcome_difference += 1

    stateful_goal_pass_count = sum(
        1
        for result in results
        if result.summary.get("stateful_all_goals_passed") is True
    )
    stateless_goal_pass_count = sum(
        1
        for result in results
        if result.summary.get("stateless_all_goals_passed") is True
    )
    stateful_all_calls_succeeded_count = sum(
        1
        for result in results
        if result.summary.get("stateful_all_calls_succeeded") is True
    )
    stateless_all_calls_succeeded_count = sum(
        1
        for result in results
        if result.summary.get("stateless_all_calls_succeeded") is True
    )

    return OverviewMetrics(
        total_cases=total_cases,
        stateful_goal_pass_count=stateful_goal_pass_count,
        stateless_goal_pass_count=stateless_goal_pass_count,
        stateful_all_calls_succeeded_count=stateful_all_calls_succeeded_count,
        stateless_all_calls_succeeded_count=stateless_all_calls_succeeded_count,
        stateful_total_steps_sum=stateful_total_steps_sum,
        stateless_total_steps_sum=stateless_total_steps_sum,
        stateful_avg_steps=(stateful_total_steps_sum / total_cases) if total_cases else 0.0,
        stateless_avg_steps=(stateless_total_steps_sum / total_cases) if total_cases else 0.0,
        cases_with_step_count_difference=cases_with_step_count_difference,
        cases_with_explicit_dependency_resolution=cases_with_explicit_dependency_resolution,
        cases_with_query_before_index=cases_with_query_before_index,
        cases_with_overwrite_without_reindex=cases_with_overwrite_without_reindex,
        cases_with_trajectory_divergence=cases_with_trajectory_divergence,
        cases_with_snapshot_semantics_difference=cases_with_snapshot_semantics_difference,
        cases_with_retrieval_outcome_difference=cases_with_retrieval_outcome_difference,
    )


def generate_overall_conclusion(overview_metrics: OverviewMetrics) -> str:
    sentences: List[str] = []

    if overview_metrics.cases_with_explicit_dependency_resolution > 0 or overview_metrics.stateful_avg_steps > overview_metrics.stateless_avg_steps:
        sentences.append(
            "Across the evaluated cases, the stateful setting introduced explicit dependency-management steps that were absent or less prominent in the stateless baseline."
        )

    if overview_metrics.cases_with_trajectory_divergence > 0:
        sentences.append(
            "The two settings also exhibited stable trajectory-level divergence, indicating that the stateful formulation changes the tool-use process rather than only the final outcome."
        )

    if overview_metrics.cases_with_snapshot_semantics_difference > 0:
        sentences.append(
            "The stateful environment preserved index-time snapshot semantics in cases involving overwrite without re-index, whereas the stateless baseline reflected only the latest file content."
        )

    if overview_metrics.cases_with_retrieval_outcome_difference > 0:
        sentences.append(
            "These process differences were accompanied by retrieval outcome differences in a subset of cases."
        )

    if not sentences:
        sentences.append(
            "Across the evaluated cases, the stateless and stateful settings showed limited aggregate differences under the current minimal prototype."
        )

    return " ".join(sentences[:3])


def _has_snapshot_semantics_difference(result: ComparisonResult, trajectory: Any) -> bool:
    if "overwrite-without-reindex" not in trajectory.key_process_difference:
        return False
    stateful_hits = _extract_last_query_hits(result.stateful_result.trace)
    stateless_hits = _extract_last_query_hits(result.stateless_result.trace)
    return bool(stateful_hits) and not bool(stateless_hits)


def _has_retrieval_outcome_difference(result: ComparisonResult) -> bool:
    stateful_hits = _normalize_hits(_extract_last_query_hits(result.stateful_result.trace))
    stateless_hits = _normalize_hits(_extract_last_query_hits(result.stateless_result.trace))
    return stateful_hits != stateless_hits


def _extract_last_query_hits(trace: Sequence[Any]) -> List[Dict[str, Any]]:
    for record in reversed(list(trace)):
        if record.tool_name == "search.query":
            return record.observation.get("hits", [])
    return []


def _normalize_hits(hits: List[Dict[str, Any]]) -> List[tuple]:
    normalized = []
    for hit in hits:
        normalized.append((hit.get("file_id"), hit.get("content")))
    return normalized
