"""
Unit tests for toolsim.trajectory_evaluator.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toolsim.runners.comparison_runner import ComparisonRunner, build_stateless_vs_stateful_cases
from toolsim.reporting.reporting import BatchComparisonRunner, render_markdown_report
from toolsim.evaluators.trajectory_evaluator import TrajectoryLevelEvaluator, summarize_trajectory_difference


def test_trajectory_metrics_counts_steps_and_sequence():
    case = build_stateless_vs_stateful_cases()[1]
    result = ComparisonRunner().run_case(case)
    metrics = TrajectoryLevelEvaluator().evaluate(result.stateful_result.trace)

    assert metrics.total_steps == 3
    assert metrics.tool_sequence == ["file.write", "search.index", "search.query"]


def test_trajectory_metrics_detects_repeated_calls():
    case = build_stateless_vs_stateful_cases()[2]
    result = ComparisonRunner().run_case(case)
    metrics = TrajectoryLevelEvaluator().evaluate(result.stateful_result.trace)

    assert metrics.repeated_calls["file.write"] == 2


def test_trajectory_metrics_detects_contains_index_step():
    case = build_stateless_vs_stateful_cases()[1]
    result = ComparisonRunner().run_case(case)
    metrics = TrajectoryLevelEvaluator().evaluate(result.stateful_result.trace)

    assert metrics.contains_index_step is True


def test_detects_query_before_index_pattern():
    case = build_stateless_vs_stateful_cases()[0]
    result = ComparisonRunner().run_case(case)
    metrics = TrajectoryLevelEvaluator().evaluate(result.stateful_result.trace)

    assert metrics.query_before_index_detected is True


def test_detects_explicit_dependency_resolution_pattern():
    case = build_stateless_vs_stateful_cases()[1]
    result = ComparisonRunner().run_case(case)
    metrics = TrajectoryLevelEvaluator().evaluate(result.stateful_result.trace)

    assert metrics.explicit_dependency_resolution_detected is True


def test_detects_overwrite_without_reindex_pattern():
    case = build_stateless_vs_stateful_cases()[2]
    result = ComparisonRunner().run_case(case)
    metrics = TrajectoryLevelEvaluator().evaluate(result.stateful_result.trace)

    assert metrics.overwrite_without_reindex_detected is True


def test_comparison_level_trajectory_difference_text_is_reasonable():
    results = [ComparisonRunner().run_case(case) for case in build_stateless_vs_stateful_cases()]
    summaries = [summarize_trajectory_difference(result) for result in results]

    assert "directly searched current file content" in summaries[0].key_process_difference
    assert "explicit indexing" in summaries[1].key_process_difference
    assert "overwrite-without-reindex" in summaries[2].key_process_difference


def test_markdown_report_contains_step_counts_or_sequences():
    report = render_markdown_report(BatchComparisonRunner().run(build_stateless_vs_stateful_cases()))

    assert "Stateful steps:" in report
    assert "Stateful sequence:" in report


def run_all_tests() -> None:
    test_trajectory_metrics_counts_steps_and_sequence()
    test_trajectory_metrics_detects_repeated_calls()
    test_trajectory_metrics_detects_contains_index_step()
    test_detects_query_before_index_pattern()
    test_detects_explicit_dependency_resolution_pattern()
    test_detects_overwrite_without_reindex_pattern()
    test_comparison_level_trajectory_difference_text_is_reasonable()
    test_markdown_report_contains_step_counts_or_sequences()
    print("All trajectory_evaluator tests passed!")


if __name__ == "__main__":
    run_all_tests()
