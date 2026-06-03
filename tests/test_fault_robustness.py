"""Unit tests for fault robustness runner and report."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toolsim.reporting.fault_report import render_fault_robustness_markdown
from toolsim.runners.fault_robustness import (
    FaultRobustnessRunner,
    build_default_fault_robustness_cases,
    build_experiment1_noise_robustness_cases,
)


def test_default_fault_robustness_suite_runs_all_cases():
    cases = build_default_fault_robustness_cases()
    result = FaultRobustnessRunner().run(cases)

    assert len(cases) == 4
    assert len(result.results) == 4
    assert result.metrics is not None
    assert result.metrics.total_cases == 4
    assert result.metrics.success_rate == 1.0
    assert result.metrics.success_at_1 < result.metrics.pass_k


def test_fault_robustness_detects_recovery_and_extra_steps():
    result = FaultRobustnessRunner().run(build_default_fault_robustness_cases())
    by_name = {case_result.case.case_name: case_result for case_result in result.results}

    transient = by_name["transient_file_write_recovery"]
    vague = by_name["vague_issue_error_recovery"]

    assert transient.recovery_detected is True
    assert transient.extra_steps == 1
    assert vague.recovery_detected is True
    assert vague.observation_fault_count == 1


def test_fault_robustness_report_renders_key_metrics():
    result = FaultRobustnessRunner().run(build_default_fault_robustness_cases())
    report = render_fault_robustness_markdown(result)

    assert "# Fault Robustness Report" in report
    assert "Success@1:" in report
    assert "Pass^k:" in report
    assert "Success rate: 100.0%" in report
    assert "Recovery rate: 100.0%" in report
    assert "stale_search_observation" in report


def test_experiment1_noise_suite_builds_synthetic_cases():
    cases = build_experiment1_noise_robustness_cases(include_toolsandbox=False)
    result = FaultRobustnessRunner().run(cases)

    assert len(cases) == 36
    assert result.metrics is not None
    assert set(result.metrics.by_noise_type) == {
        "schema_drift",
        "stale_state",
        "timeout",
        "vague_observation",
    }
    assert result.metrics.pass_k >= result.metrics.success_at_1
