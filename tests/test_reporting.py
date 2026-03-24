"""
Unit tests for toolsim.reporting.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toolsim.runners.comparison_runner import ComparisonRunner, build_stateless_vs_stateful_cases
from toolsim.reporting.reporting import BatchComparisonRunner, render_markdown_report, summarize_comparison_result


def test_batch_comparison_runner_returns_batch_result():
    cases = build_stateless_vs_stateful_cases()
    batch_result = BatchComparisonRunner().run(cases)

    assert batch_result.total_cases == 3
    assert len(batch_result.results) == 3
    assert len(batch_result.summaries) == 3


def test_batch_result_counts_are_correct():
    cases = build_stateless_vs_stateful_cases()
    batch_result = BatchComparisonRunner().run(cases)

    assert batch_result.stateful_goal_pass_count == 3
    assert batch_result.stateless_goal_pass_count == 3
    assert batch_result.stateful_all_calls_succeeded_count == 3
    assert batch_result.stateless_all_calls_succeeded_count == 3


def test_single_comparison_result_can_export_dict():
    case = build_stateless_vs_stateful_cases()[0]
    result = ComparisonRunner().run_case(case)
    payload = result.to_dict()

    assert payload["case_name"] == case.case_name
    assert "stateful_result" in payload
    assert "stateless_result" in payload


def test_batch_comparison_result_can_export_dict():
    cases = build_stateless_vs_stateful_cases()
    batch_result = BatchComparisonRunner().run(cases)
    payload = batch_result.to_dict()

    assert payload["total_cases"] == 3
    assert len(payload["results"]) == 3
    assert len(payload["summaries"]) == 3


def test_markdown_report_renders_string():
    batch_result = BatchComparisonRunner().run(build_stateless_vs_stateful_cases())
    report = render_markdown_report(batch_result)

    assert isinstance(report, str)
    assert len(report) > 0


def test_markdown_report_contains_title_and_case_name():
    batch_result = BatchComparisonRunner().run(build_stateless_vs_stateful_cases())
    report = render_markdown_report(batch_result)

    assert "# Stateless vs Stateful Comparison Report" in report
    assert "write_then_query" in report


def test_key_difference_rules_cover_existing_cases():
    cases = build_stateless_vs_stateful_cases()
    runner = ComparisonRunner()

    summaries = [summarize_comparison_result(case, runner.run_case(case)) for case in cases]

    assert "not indexed" in summaries[0].key_difference
    assert "explicit indexing" in summaries[1].key_difference
    assert "indexed snapshot" in summaries[2].key_difference


def run_all_tests() -> None:
    test_batch_comparison_runner_returns_batch_result()
    test_batch_result_counts_are_correct()
    test_single_comparison_result_can_export_dict()
    test_batch_comparison_result_can_export_dict()
    test_markdown_report_renders_string()
    test_markdown_report_contains_title_and_case_name()
    test_key_difference_rules_cover_existing_cases()
    print("All reporting tests passed!")


if __name__ == "__main__":
    run_all_tests()
