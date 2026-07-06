"""Tests for ToolSandbox benchmark runner and reporting."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toolsandbox_fixture_utils import TOOLSANDBOX_JSON_PATH, clone_toolsandbox_case, expand_cases_per_domain
from toolsim.adapters.toolsandbox_adapter import convert_toolsandbox_file, select_toolsandbox_subset_cases
from toolsim.reporting.toolsandbox_report import render_toolsandbox_benchmark_markdown
from toolsim.runners.toolsandbox_benchmark import ToolSandboxBenchmarkRunner


def test_toolsandbox_oracle_benchmark_runs_subset_successfully():
    cases = [case for case in convert_toolsandbox_file(TOOLSANDBOX_JSON_PATH) if case.goals]
    benchmark = ToolSandboxBenchmarkRunner().run(cases)

    assert benchmark.metrics.total_cases == len(cases)
    assert benchmark.metrics.goal_cases == len(cases)
    assert benchmark.metrics.success_rate == 1.0
    assert benchmark.metrics.invalid_call_rate == 0.0
    assert "contacts" in benchmark.metrics.by_domain


def test_toolsandbox_benchmark_detects_minefield_violation():
    case = next(case for case in convert_toolsandbox_file(TOOLSANDBOX_JSON_PATH) if case.minefield_goals)

    def bad_provider(_case):
        fields = _case.minefield_goals[0]["fields"]
        return [{"tool_name": "end_conversation", "args": {"content": fields["content"], "recipient": fields["recipient"]}}]

    benchmark = ToolSandboxBenchmarkRunner().run([case], tool_call_provider=bad_provider, mode="bad_agent")

    assert benchmark.metrics.minefield_cases == 1
    assert benchmark.metrics.minefield_violation_count == 1
    assert benchmark.metrics.minefield_violation_rate == 1.0
    assert benchmark.results[0].minefield_violation is True


def test_toolsandbox_report_contains_group_tables_and_failures():
    cases = [case for case in convert_toolsandbox_file(TOOLSANDBOX_JSON_PATH) if case.goals]
    benchmark = ToolSandboxBenchmarkRunner().run(cases)
    report = render_toolsandbox_benchmark_markdown(benchmark)

    assert "# ToolSandbox Benchmark Report" in report
    assert "## By Domain" in report
    assert "## By Category" in report
    assert "No goal failures" in report


def test_toolsandbox_subset_sampler_selects_domain_balanced_cases():
    source = convert_toolsandbox_file(TOOLSANDBOX_JSON_PATH)
    goal_cases = [case for case in source if case.goals]
    cases = expand_cases_per_domain(goal_cases, per_domain=5)
    minefield = next(case for case in source if case.minefield_goals)
    cases.append(clone_toolsandbox_case(minefield, "minefield"))
    subset = select_toolsandbox_subset_cases(cases, group_by="domain", per_group=5)

    counts = {}
    for case in subset:
        counts[case.domain] = counts.get(case.domain, 0) + 1

    assert len(subset) == 25
    assert set(counts) == {"contacts", "device_settings", "external_search", "messaging", "reminders"}
    assert all(count == 5 for count in counts.values())
    assert any(case.minefield_goals for case in subset)


def test_toolsandbox_subset_benchmark_runs_successfully():
    source = [case for case in convert_toolsandbox_file(TOOLSANDBOX_JSON_PATH) if case.goals]
    cases = select_toolsandbox_subset_cases(expand_cases_per_domain(source, per_domain=5), group_by="domain", per_group=5)
    benchmark = ToolSandboxBenchmarkRunner().run(cases, mode="oracle_subset_by_domain_5")

    assert benchmark.metrics.total_cases == 25
    assert benchmark.metrics.goal_cases > 0
    assert benchmark.metrics.success_rate == 1.0
