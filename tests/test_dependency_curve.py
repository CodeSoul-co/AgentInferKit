"""Tests for synthetic cross-tool dependency difficulty curve experiments."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toolsim.reporting.dependency_curve_report import render_dependency_curve_markdown
from toolsim.adapters.toolsandbox_adapter import convert_toolsandbox_file
from toolsim.runners.dependency_curve import (
    DEFAULT_STRATEGIES,
    L1_SINGLE_TOOL,
    L2_EXPLICIT_DEP,
    L3_IMPLICIT_SIDE_EFFECT,
    DependencyCurveRunner,
    build_synthetic_dependency_curve_cases,
    build_toolsandbox_dependency_curve_cases,
    select_toolsandbox_dependency_subset_cases,
)


ROOT = Path(__file__).parent.parent
TOOLSANDBOX_JSON_PATH = ROOT / "Toolsandbox" / "tool_sandbox_scenarios.json"


def test_build_synthetic_dependency_curve_cases_has_balanced_levels():
    cases = build_synthetic_dependency_curve_cases()
    counts = {}
    for case in cases:
        counts[case.difficulty_level] = counts.get(case.difficulty_level, 0) + 1

    assert len(cases) == 15
    assert counts == {
        L1_SINGLE_TOOL: 5,
        L2_EXPLICIT_DEP: 5,
        L3_IMPLICIT_SIDE_EFFECT: 5,
    }


def test_dependency_curve_runner_reports_degradation_trend():
    result = DependencyCurveRunner().run(build_synthetic_dependency_curve_cases())
    summaries = {summary.strategy: summary for summary in result.strategy_summaries}

    assert set(summaries) == set(DEFAULT_STRATEGIES)
    assert summaries["direct"].l1_success_rate == 1.0
    assert summaries["direct"].l3_success_rate < summaries["direct"].l1_success_rate
    assert summaries["self_refine"].l3_success_rate == 1.0
    assert summaries["direct"].degradation_l1_to_l3 > summaries["react"].degradation_l1_to_l3
    assert summaries["react"].degradation_l1_to_l3 >= summaries["self_refine"].degradation_l1_to_l3


def test_dependency_curve_group_metrics_capture_dependency_errors():
    result = DependencyCurveRunner().run(build_synthetic_dependency_curve_cases())
    direct_l3 = next(
        metric
        for metric in result.group_metrics
        if metric.strategy == "direct" and metric.difficulty_level == L3_IMPLICIT_SIDE_EFFECT
    )
    self_refine_l3 = next(
        metric
        for metric in result.group_metrics
        if metric.strategy == "self_refine" and metric.difficulty_level == L3_IMPLICIT_SIDE_EFFECT
    )

    assert direct_l3.missing_prerequisite_rate > 0
    assert direct_l3.side_effect_awareness_rate < self_refine_l3.side_effect_awareness_rate
    assert self_refine_l3.recovery_rate > 0


def test_dependency_curve_markdown_report_renders_summary_tables():
    result = DependencyCurveRunner().run(build_synthetic_dependency_curve_cases())
    report = render_dependency_curve_markdown(result)

    assert "# Cross-tool Dependency Difficulty Curve Report" in report
    assert "## Strategy Degradation" in report
    assert "## Metrics By Difficulty" in report
    assert "direct" in report


def test_toolsandbox_dependency_subset_selects_balanced_levels():
    source_cases = [case for case in convert_toolsandbox_file(TOOLSANDBOX_JSON_PATH) if case.goals]
    subset = select_toolsandbox_dependency_subset_cases(source_cases, per_level=8)
    curve_cases = build_toolsandbox_dependency_curve_cases(subset)

    counts = {}
    for case in curve_cases:
        counts[case.difficulty_level] = counts.get(case.difficulty_level, 0) + 1

    assert len(subset) == 24
    assert len(curve_cases) == 24
    assert counts == {
        L1_SINGLE_TOOL: 8,
        L2_EXPLICIT_DEP: 8,
        L3_IMPLICIT_SIDE_EFFECT: 8,
    }


def test_toolsandbox_dependency_curve_runs_all_strategies():
    source_cases = [case for case in convert_toolsandbox_file(TOOLSANDBOX_JSON_PATH) if case.goals]
    subset = select_toolsandbox_dependency_subset_cases(source_cases, per_level=5)
    result = DependencyCurveRunner().run(build_toolsandbox_dependency_curve_cases(subset))
    summaries = {summary.strategy: summary for summary in result.strategy_summaries}

    assert len(result.results) == 5 * 3 * len(DEFAULT_STRATEGIES)
    assert summaries["direct"].l1_success_rate >= summaries["direct"].l3_success_rate
    assert summaries["self_refine"].auc_success >= summaries["direct"].auc_success


def run_all_tests() -> None:
    test_build_synthetic_dependency_curve_cases_has_balanced_levels()
    test_dependency_curve_runner_reports_degradation_trend()
    test_dependency_curve_group_metrics_capture_dependency_errors()
    test_dependency_curve_markdown_report_renders_summary_tables()
    test_toolsandbox_dependency_subset_selects_balanced_levels()
    test_toolsandbox_dependency_curve_runs_all_strategies()
    print("All dependency_curve tests passed!")


if __name__ == "__main__":
    run_all_tests()
