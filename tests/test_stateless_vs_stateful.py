"""
Unit tests for Stateless vs Stateful comparison experiments.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toolsandbox_fixture_utils import TOOLSANDBOX_JSON_PATH, expand_cases_per_domain
from toolsim.adapters.toolsandbox_adapter import convert_toolsandbox_file
from toolsim.runners.comparison_runner import (
    ComparisonRunner,
    build_stateless_vs_stateful_cases,
    build_toolsandbox_stateless_vs_stateful_cases,
    select_toolsandbox_comparison_subset_cases,
)


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


def test_case_issue_close_requires_recovery_in_stateful_only():
    case = build_stateless_vs_stateful_cases()[3]
    result = ComparisonRunner().run_case(case)

    stateful_tools = [record.tool_name for record in result.stateful_result.trace]
    stateless_tools = [record.tool_name for record in result.stateless_result.trace]

    assert stateful_tools == ["issue.create", "issue.close", "issue.assign", "issue.close"]
    assert stateless_tools == ["issue.create", "issue.close"]
    assert result.stateful_result.trace[1].success is False
    assert result.stateful_result.trace[3].success is True
    assert result.stateless_result.trace[1].success is True
    assert result.stateful_result.final_state.get_entity("issue", "iss1")["assignee"] == "bob"
    assert result.stateless_result.final_state.get_entity("issue", "iss1")["assignee"] is None


def test_comparison_runner_can_build_readable_summary():
    cases = build_stateless_vs_stateful_cases()
    summaries = ComparisonRunner().run_cases_with_readable_summary(cases)

    assert len(summaries) == 9
    assert summaries[0]["case_name"] == "write_then_query"
    assert summaries[0]["stateful_final_hits"] == []
    assert len(summaries[0]["stateless_final_hits"]) == 1


def test_case_multi_file_partial_index_only_searches_indexed_files_statefully():
    case = build_stateless_vs_stateful_cases()[4]
    result = ComparisonRunner().run_case(case)

    stateful_hits = result.stateful_result.trace[-1].observation["hits"]
    stateless_hits = result.stateless_result.trace[-1].observation["hits"]

    assert [hit["file_id"] for hit in stateful_hits] == ["f1"]
    assert [hit["file_id"] for hit in stateless_hits] == ["f1", "f2"]


def test_case_reindex_after_overwrite_updates_stateful_snapshot():
    case = build_stateless_vs_stateful_cases()[5]
    result = ComparisonRunner().run_case(case)

    stateful_hits = result.stateful_result.trace[-1].observation["hits"]
    stateless_hits = result.stateless_result.trace[-1].observation["hits"]

    assert len(stateful_hits) == 1
    assert stateful_hits[0]["content"] == "new beta"
    assert len(stateless_hits) == 1
    assert stateless_hits[0]["content"] == "new beta"
    assert result.stateful_result.trace[3].tool_name == "search.index"


def test_case_calendar_conflict_requires_stateful_reschedule():
    case = build_stateless_vs_stateful_cases()[6]
    result = ComparisonRunner().run_case(case)

    assert result.stateful_result.trace[1].success is False
    assert result.stateful_result.trace[2].success is True
    assert result.stateful_result.final_state.get_entity("calendar_event", "e2")["start_time"] == 11.0
    assert result.stateless_result.final_state.get_entity("calendar_event", "e2")["start_time"] == 10.5


def test_case_calendar_update_conflict_requires_stateful_recovery():
    case = build_stateless_vs_stateful_cases()[7]
    result = ComparisonRunner().run_case(case)

    assert result.stateful_result.trace[2].success is False
    assert result.stateful_result.trace[3].success is True
    assert result.stateful_result.final_state.get_entity("calendar_event", "e2")["start_time"] == 11.0
    assert result.stateless_result.final_state.get_entity("calendar_event", "e2")["start_time"] == 9.5


def test_case_issue_reopen_requires_closed_state_in_stateful_only():
    case = build_stateless_vs_stateful_cases()[8]
    result = ComparisonRunner().run_case(case)

    assert result.stateful_result.trace[1].success is False
    assert result.stateful_result.trace[4].success is True
    assert result.stateless_result.trace[1].success is True
    assert result.stateful_result.final_state.get_entity("issue", "iss2")["assignee"] == "bob"
    assert result.stateless_result.final_state.get_entity("issue", "iss2")["assignee"] is None


def test_toolsandbox_comparison_subset_selects_eight_goal_cases_per_domain():
    source_cases = [case for case in convert_toolsandbox_file(TOOLSANDBOX_JSON_PATH) if case.goals]
    expanded_cases = expand_cases_per_domain(source_cases, per_domain=5)
    subset = select_toolsandbox_comparison_subset_cases(expanded_cases, group_by="domain", per_group=5)
    comparison_cases = build_toolsandbox_stateless_vs_stateful_cases(subset)

    counts = {}
    for case in subset:
        counts[case.domain] = counts.get(case.domain, 0) + 1

    assert len(subset) == 25
    assert len(comparison_cases) == 25
    assert set(counts) == {"contacts", "device_settings", "external_search", "messaging", "reminders"}
    assert all(count == 5 for count in counts.values())


def test_toolsandbox_comparison_subset_runs_with_final_state_correctness():
    source_cases = [case for case in convert_toolsandbox_file(TOOLSANDBOX_JSON_PATH) if case.goals]
    subset = select_toolsandbox_comparison_subset_cases(expand_cases_per_domain(source_cases, per_domain=5), group_by="domain", per_group=5)
    comparison_cases = build_toolsandbox_stateless_vs_stateful_cases(subset)
    results = ComparisonRunner().run_cases(comparison_cases)

    assert len(results) == 25
    assert all(result.summary["stateful_all_goals_passed"] is True for result in results)
    assert all(result.summary["stateless_all_goals_passed"] is True for result in results)
    assert sum(len(result.stateful_result.trace) for result in results) > sum(
        len(result.stateless_result.trace) for result in results
    )


def run_all_tests() -> None:
    test_case_write_then_query_differs_between_stateful_and_stateless()
    test_case_write_index_query_hits_in_both_settings()
    test_case_overwrite_without_reindex_shows_stale_vs_current_difference()
    test_comparison_runner_returns_structured_result()
    test_case_issue_close_requires_recovery_in_stateful_only()
    test_comparison_runner_can_build_readable_summary()
    test_case_multi_file_partial_index_only_searches_indexed_files_statefully()
    test_case_reindex_after_overwrite_updates_stateful_snapshot()
    test_case_calendar_conflict_requires_stateful_reschedule()
    test_case_calendar_update_conflict_requires_stateful_recovery()
    test_case_issue_reopen_requires_closed_state_in_stateful_only()
    test_toolsandbox_comparison_subset_selects_eight_goal_cases_per_domain()
    test_toolsandbox_comparison_subset_runs_with_final_state_correctness()
    print("All stateless_vs_stateful tests passed!")


if __name__ == "__main__":
    run_all_tests()
