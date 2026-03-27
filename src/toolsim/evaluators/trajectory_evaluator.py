"""Trajectory-level evaluator: analyses entire execution traces for patterns."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from toolsim.core.utils import extract_last_query_hits
from toolsim.execution.stateful_executor import ExecutionRecord
from toolsim.execution.stateful_tracer import TraceRecorder
from toolsim.runners.comparison_runner import ComparisonResult


@dataclass
class TrajectoryMetrics:
    """Aggregate trajectory-level statistics for a sequence of execution records."""

    total_steps: int
    tool_sequence: list[str]
    unique_tools: list[str]
    repeated_calls: dict[str, int]
    contains_index_step: bool
    read_only_call_count: int
    state_changing_call_count: int
    first_failure_step: int | None
    successful_steps: int
    failed_steps: int
    query_before_index_detected: bool
    explicit_dependency_resolution_detected: bool
    overwrite_without_reindex_detected: bool
    issue_close_recovery_detected: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_steps": self.total_steps,
            "tool_sequence": self.tool_sequence,
            "unique_tools": self.unique_tools,
            "repeated_calls": self.repeated_calls,
            "contains_index_step": self.contains_index_step,
            "read_only_call_count": self.read_only_call_count,
            "state_changing_call_count": self.state_changing_call_count,
            "first_failure_step": self.first_failure_step,
            "successful_steps": self.successful_steps,
            "failed_steps": self.failed_steps,
            "query_before_index_detected": self.query_before_index_detected,
            "explicit_dependency_resolution_detected": self.explicit_dependency_resolution_detected,
            "overwrite_without_reindex_detected": self.overwrite_without_reindex_detected,
            "issue_close_recovery_detected": self.issue_close_recovery_detected,
        }


@dataclass
class TrajectoryComparisonSummary:
    """Side-by-side trajectory comparison between stateful and stateless runs."""

    stateful_total_steps: int
    stateless_total_steps: int
    step_count_difference: int
    stateful_contains_index_step: bool
    stateless_contains_index_step: bool
    key_process_difference: str
    stateful_tool_sequence: list[str]
    stateless_tool_sequence: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "stateful_total_steps": self.stateful_total_steps,
            "stateless_total_steps": self.stateless_total_steps,
            "step_count_difference": self.step_count_difference,
            "stateful_contains_index_step": self.stateful_contains_index_step,
            "stateless_contains_index_step": self.stateless_contains_index_step,
            "key_process_difference": self.key_process_difference,
            "stateful_tool_sequence": self.stateful_tool_sequence,
            "stateless_tool_sequence": self.stateless_tool_sequence,
        }


class TrajectoryLevelEvaluator:
    """Compute trajectory-level statistics and detect execution patterns from traces."""

    def evaluate(self, records_or_tracer: Sequence[ExecutionRecord] | TraceRecorder) -> TrajectoryMetrics:
        records = _normalize_records(records_or_tracer)
        tool_sequence = [record.tool_name for record in records]
        counts: dict[str, int] = {}
        for tool_name in tool_sequence:
            counts[tool_name] = counts.get(tool_name, 0) + 1

        repeated_calls = {tool_name: count for tool_name, count in counts.items() if count > 1}
        contains_index_step = "search.index" in tool_sequence
        read_only_call_count = sum(1 for record in records if not record.state_changed)
        state_changing_call_count = sum(1 for record in records if record.state_changed)
        failed_steps = sum(1 for record in records if not record.success)
        successful_steps = len(records) - failed_steps
        first_failure_step = next((idx + 1 for idx, record in enumerate(records) if not record.success), None)

        return TrajectoryMetrics(
            total_steps=len(records),
            tool_sequence=tool_sequence,
            unique_tools=list(dict.fromkeys(tool_sequence).keys()),
            repeated_calls=repeated_calls,
            contains_index_step=contains_index_step,
            read_only_call_count=read_only_call_count,
            state_changing_call_count=state_changing_call_count,
            first_failure_step=first_failure_step,
            successful_steps=successful_steps,
            failed_steps=failed_steps,
            query_before_index_detected=detect_query_before_index(records),
            explicit_dependency_resolution_detected=detect_explicit_dependency_resolution(records),
            overwrite_without_reindex_detected=detect_overwrite_without_reindex_pattern(records),
            issue_close_recovery_detected=detect_issue_close_recovery_pattern(records),
        )


def detect_query_before_index(records_or_tracer: Sequence[ExecutionRecord] | TraceRecorder) -> bool:
    records = _normalize_records(records_or_tracer)
    seen_write = False
    seen_index = False
    for record in records:
        if record.tool_name == "file.write":
            seen_write = True
        elif record.tool_name == "search.index":
            seen_index = True
        elif record.tool_name == "search.query" and seen_write and not seen_index:
            return True
    return False


def detect_explicit_dependency_resolution(records_or_tracer: Sequence[ExecutionRecord] | TraceRecorder) -> bool:
    records = _normalize_records(records_or_tracer)
    seen_index = False
    for record in records:
        if record.tool_name == "search.index":
            seen_index = True
        elif record.tool_name == "search.query" and seen_index:
            return True
    return False


def detect_issue_close_recovery_pattern(records_or_tracer: Sequence[ExecutionRecord] | TraceRecorder) -> bool:
    records = _normalize_records(records_or_tracer)
    failed_close_issue_ids: set[str] = set()
    assigned_issue_ids: set[str] = set()

    for record in records:
        issue_id = record.args.get("issue_id")
        if record.tool_name == "issue.close" and not record.success and issue_id:
            failed_close_issue_ids.add(issue_id)
        elif record.tool_name == "issue.assign" and record.success and issue_id in failed_close_issue_ids:
            assigned_issue_ids.add(issue_id)
        elif record.tool_name == "issue.close" and record.success and issue_id in assigned_issue_ids:
            return True
    return False


def detect_overwrite_without_reindex_pattern(records_or_tracer: Sequence[ExecutionRecord] | TraceRecorder) -> bool:
    records = _normalize_records(records_or_tracer)
    file_states: dict[str, dict[str, bool]] = {}

    for record in records:
        if record.tool_name == "file.write":
            file_id = record.args.get("file_id")
            if file_id is None:
                continue
            state = file_states.setdefault(file_id, {"wrote": False, "indexed": False, "overwrote_after_index": False})
            if state["indexed"]:
                state["overwrote_after_index"] = True
            state["wrote"] = True
        elif record.tool_name == "search.index":
            file_id = record.args.get("file_id")
            if file_id is None:
                continue
            state = file_states.setdefault(file_id, {"wrote": False, "indexed": False, "overwrote_after_index": False})
            if state["wrote"]:
                state["indexed"] = True
        elif record.tool_name == "search.query":
            if any(state["indexed"] and state["overwrote_after_index"] for state in file_states.values()):
                return True
    return False


def summarize_trajectory_difference(comparison_result: ComparisonResult) -> TrajectoryComparisonSummary:
    """Summarise the key trajectory-level differences between stateful and stateless runs."""
    evaluator = TrajectoryLevelEvaluator()
    stateful_metrics = evaluator.evaluate(comparison_result.stateful_result.trace)
    stateless_metrics = evaluator.evaluate(comparison_result.stateless_result.trace)

    return TrajectoryComparisonSummary(
        stateful_total_steps=stateful_metrics.total_steps,
        stateless_total_steps=stateless_metrics.total_steps,
        step_count_difference=stateful_metrics.total_steps - stateless_metrics.total_steps,
        stateful_contains_index_step=stateful_metrics.contains_index_step,
        stateless_contains_index_step=stateless_metrics.contains_index_step,
        key_process_difference=_build_key_process_difference(comparison_result, stateful_metrics, stateless_metrics),
        stateful_tool_sequence=stateful_metrics.tool_sequence,
        stateless_tool_sequence=stateless_metrics.tool_sequence,
    )


def _build_key_process_difference(
    comparison_result: ComparisonResult,
    stateful_metrics: TrajectoryMetrics,
    stateless_metrics: TrajectoryMetrics,
) -> str:
    stateful_hits = extract_last_query_hits(comparison_result.stateful_result.trace)
    stateless_hits = extract_last_query_hits(comparison_result.stateless_result.trace)

    if not stateful_hits and stateless_hits:
        return (
            "Stateful trajectory queried before dependency completion, while stateless trajectory directly searched "
            "current file content."
        )
    if stateful_metrics.overwrite_without_reindex_detected and not stateless_metrics.overwrite_without_reindex_detected:
        return (
            "Stateful trajectory preserved an overwrite-without-reindex structure, while stateless trajectory always "
            "followed the latest file content."
        )
    if stateful_metrics.explicit_dependency_resolution_detected and not stateless_metrics.contains_index_step:
        return "Stateful trajectory included explicit indexing before retrieval, while stateless trajectory did not."
    if stateful_metrics.total_steps != stateless_metrics.total_steps:
        return "Stateful trajectory required an extra dependency-resolution step."
    return "Stateful and stateless trajectories were structurally similar in this case."


# Re-export for backwards compatibility with internal callers
_extract_last_query_hits = extract_last_query_hits


def _normalize_records(records_or_tracer: Sequence[ExecutionRecord] | TraceRecorder) -> list[ExecutionRecord]:
    if isinstance(records_or_tracer, TraceRecorder):
        return records_or_tracer.get_records()
    return list(records_or_tracer)
