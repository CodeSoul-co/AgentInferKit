"""Tests for ToolSandbox benchmark runner and reporting."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toolsim.adapters.toolsandbox_adapter import convert_toolsandbox_file, select_toolsandbox_subset_cases
from toolsim.reporting.toolsandbox_report import render_toolsandbox_benchmark_markdown
from toolsim.runners.toolsandbox_benchmark import ToolSandboxBenchmarkRunner


ROOT = Path(__file__).parent.parent
JSON_PATH = ROOT / "Toolsandbox" / "tool_sandbox_scenarios.json"


def test_toolsandbox_oracle_benchmark_runs_subset_successfully():
    cases = [case for case in convert_toolsandbox_file(JSON_PATH, limit=20) if case.goals]
    benchmark = ToolSandboxBenchmarkRunner().run(cases)

    assert benchmark.metrics.total_cases == len(cases)
    assert benchmark.metrics.goal_cases == len(cases)
    assert benchmark.metrics.success_rate == 1.0
    assert benchmark.metrics.invalid_call_rate == 0.0
    assert "contacts" in benchmark.metrics.by_domain


def test_toolsandbox_benchmark_detects_minefield_violation():
    case = next(case for case in convert_toolsandbox_file(JSON_PATH) if case.minefield_goals)

    def bad_provider(_case):
        fields = _case.minefield_goals[0]["fields"]
        return [{"tool_name": "end_conversation", "args": {"content": fields["content"], "recipient": fields["recipient"]}}]

    benchmark = ToolSandboxBenchmarkRunner().run([case], tool_call_provider=bad_provider, mode="bad_agent")

    assert benchmark.metrics.minefield_cases == 1
    assert benchmark.metrics.minefield_violation_count == 1
    assert benchmark.metrics.minefield_violation_rate == 1.0
    assert benchmark.results[0].minefield_violation is True


def test_toolsandbox_report_contains_group_tables_and_failures():
    cases = [case for case in convert_toolsandbox_file(JSON_PATH, limit=20) if case.goals]
    benchmark = ToolSandboxBenchmarkRunner().run(cases)
    report = render_toolsandbox_benchmark_markdown(benchmark)

    assert "# ToolSandbox Benchmark Report" in report
    assert "## By Domain" in report
    assert "## By Category" in report
    assert "No goal failures" in report


def test_toolsandbox_subset_sampler_selects_domain_balanced_cases():
    cases = convert_toolsandbox_file(JSON_PATH)
    subset = select_toolsandbox_subset_cases(cases, group_by="domain", per_group=8)

    counts = {}
    for case in subset:
        counts[case.domain] = counts.get(case.domain, 0) + 1

    assert len(subset) == 40
    assert set(counts) == {"contacts", "device_settings", "external_search", "messaging", "reminders"}
    assert all(5 <= count <= 10 for count in counts.values())
    assert any(case.minefield_goals for case in subset)


def test_toolsandbox_subset_benchmark_runs_successfully():
    cases = select_toolsandbox_subset_cases(convert_toolsandbox_file(JSON_PATH), group_by="domain", per_group=8)
    benchmark = ToolSandboxBenchmarkRunner().run(cases, mode="oracle_subset_by_domain_8")

    assert benchmark.metrics.total_cases == 40
    assert benchmark.metrics.goal_cases > 0
    assert benchmark.metrics.success_rate == 1.0
    assert benchmark.metrics.minefield_cases > 0
    assert benchmark.metrics.minefield_violation_rate == 0.0
