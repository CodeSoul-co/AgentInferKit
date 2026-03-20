"""
Unit tests for Stateless vs Stateful comparison experiments.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toolsim.comparison_runner import ComparisonRunner, build_stateless_vs_stateful_cases


def test_case_write_then_query_differs_between_stateful_and_stateless():
    case = build_stateless_vs_stateful_cases()[0]
    result = ComparisonRunner().run_case(case)

    assert result.stateful_result.trace[-1].tool_name == "search.query"
    assert result.stateful_result.trace[-1].observation["hits"] == []
    assert len(result.stateless_result.trace[-1].observation["hits"]) == 1
    assert result.stateless_result.trace[-1].observation["hits"][0]["file_id"] == "f1"


def test_case_write_index_query_hits_in_both_settings():
    case = build_stateless_vs_stateful_cases()[1]
    result = ComparisonRunner().run_case(case)

    assert result.stateful_result.trace[1].tool_name == "search.index"
    assert len(result.stateful_result.trace[-1].observation["hits"]) == 1
    assert len(result.stateless_result.trace[-1].observation["hits"]) == 1
    assert result.stateful_result.state_metrics is not None
    assert result.stateful_result.state_metrics.all_passed is True
    assert result.stateless_result.state_metrics is not None
    assert result.stateless_result.state_metrics.all_passed is True


def test_case_overwrite_without_reindex_shows_stale_vs_current_difference():
    case = build_stateless_vs_stateful_cases()[2]
    result = ComparisonRunner().run_case(case)

    stateful_hits = result.stateful_result.trace[-1].observation["hits"]
    stateless_hits = result.stateless_result.trace[-1].observation["hits"]

    assert len(stateful_hits) == 1
    assert stateful_hits[0]["content"] == "old hello"
    assert stateless_hits == []
    assert result.stateless_result.final_state.get_entity("file", "f1")["content"] == "new gamma"


def test_comparison_runner_returns_structured_result():
    case = build_stateless_vs_stateful_cases()[0]
    result = ComparisonRunner().run_case(case)

    assert result.case_name == case.case_name
    assert result.stateful_result is not None
    assert result.stateless_result is not None
    assert "stateful_all_calls_succeeded" in result.summary
    assert "stateless_all_calls_succeeded" in result.summary


def test_comparison_runner_can_build_readable_summary():
    cases = build_stateless_vs_stateful_cases()
    summaries = ComparisonRunner().run_cases_with_readable_summary(cases)

    assert len(summaries) == 3
    assert summaries[0]["case_name"] == "write_then_query"
    assert summaries[0]["stateful_final_hits"] == []
    assert len(summaries[0]["stateless_final_hits"]) == 1


def run_all_tests() -> None:
    test_case_write_then_query_differs_between_stateful_and_stateless()
    test_case_write_index_query_hits_in_both_settings()
    test_case_overwrite_without_reindex_shows_stale_vs_current_difference()
    test_comparison_runner_returns_structured_result()
    test_comparison_runner_can_build_readable_summary()
    print("All stateless_vs_stateful tests passed!")


if __name__ == "__main__":
    run_all_tests()
