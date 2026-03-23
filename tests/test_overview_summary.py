"""
Unit tests for toolsim.overview_summary.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toolsim.comparison_runner import build_stateless_vs_stateful_cases
from toolsim.overview_summary import generate_overall_conclusion
from toolsim.reporting import BatchComparisonRunner, render_markdown_report


def test_overview_metrics_counts_total_cases():
    batch_result = BatchComparisonRunner().run(build_stateless_vs_stateful_cases())

    assert batch_result.overview_metrics.total_cases == 3


def test_overview_metrics_computes_avg_steps():
    batch_result = BatchComparisonRunner().run(build_stateless_vs_stateful_cases())

    assert batch_result.overview_metrics.stateful_avg_steps == 3.0
    assert batch_result.overview_metrics.stateless_avg_steps == 7 / 3


def test_overview_metrics_detects_step_count_difference():
    batch_result = BatchComparisonRunner().run(build_stateless_vs_stateful_cases())

    assert batch_result.overview_metrics.cases_with_step_count_difference == 2


def test_overview_metrics_detects_trajectory_divergence():
    batch_result = BatchComparisonRunner().run(build_stateless_vs_stateful_cases())

    assert batch_result.overview_metrics.cases_with_trajectory_divergence == 2


def test_overview_metrics_detects_explicit_dependency_resolution():
    batch_result = BatchComparisonRunner().run(build_stateless_vs_stateful_cases())

    assert batch_result.overview_metrics.cases_with_explicit_dependency_resolution == 1


def test_overview_metrics_detects_snapshot_semantics_difference():
    batch_result = BatchComparisonRunner().run(build_stateless_vs_stateful_cases())

    assert batch_result.overview_metrics.cases_with_snapshot_semantics_difference == 1


def test_generate_overall_conclusion_returns_non_empty_text():
    batch_result = BatchComparisonRunner().run(build_stateless_vs_stateful_cases())
    conclusion = generate_overall_conclusion(batch_result.overview_metrics)

    assert isinstance(conclusion, str)
    assert len(conclusion.strip()) > 0


def test_markdown_report_contains_overview_metrics_and_conclusion_sections():
    batch_result = BatchComparisonRunner().run(build_stateless_vs_stateful_cases())
    report = render_markdown_report(batch_result)

    assert "## Overview Metrics" in report
    assert "## Overall Conclusion" in report


def run_all_tests() -> None:
    test_overview_metrics_counts_total_cases()
    test_overview_metrics_computes_avg_steps()
    test_overview_metrics_detects_step_count_difference()
    test_overview_metrics_detects_trajectory_divergence()
    test_overview_metrics_detects_explicit_dependency_resolution()
    test_overview_metrics_detects_snapshot_semantics_difference()
    test_generate_overall_conclusion_returns_non_empty_text()
    test_markdown_report_contains_overview_metrics_and_conclusion_sections()
    print("All overview_summary tests passed!")


if __name__ == "__main__":
    run_all_tests()
