"""Tests for closed-loop agent-policy noise robustness experiments."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toolsim.runners.policy_noise_robustness import (
    PolicyNoiseRobustnessRunner,
    build_policy_noise_robustness_cases,
    render_policy_noise_markdown,
)


def test_policy_noise_suite_shows_observation_noise_degradation():
    cases = build_policy_noise_robustness_cases(include_toolsandbox=False)
    result = PolicyNoiseRobustnessRunner().run(cases)
    by_metric = {
        (item.strategy, item.noise_type): item
        for item in result.group_metrics
    }

    assert len(cases) == 75
    assert all(metric.total_cases == 15 for metric in result.group_metrics)
    assert by_metric[("direct", "vague_observation")].pass_k == 0.0
    assert by_metric[("cot", "vague_observation")].pass_k == 1.0
    assert by_metric[("cot", "stale_state")].pass_k == 0.0
    assert by_metric[("react", "stale_state")].pass_k == 1.0
    assert by_metric[("self_refine", "misleading_observation")].pass_k == 1.0


def test_policy_noise_report_renders_group_metrics():
    result = PolicyNoiseRobustnessRunner().run(build_policy_noise_robustness_cases(include_toolsandbox=False))
    report = render_policy_noise_markdown(result)

    assert "# Agent-Policy Noise Robustness Report" in report
    assert "## Noise Intensity Curve" in report
    assert "vague_observation" in report
    assert "stale_state" in report
    assert "misleading_observation" in report
    assert "self_refine" in report


def test_policy_noise_suite_includes_toolsandbox_policy_cases():
    cases = build_policy_noise_robustness_cases(include_synthetic=False, toolsandbox_per_domain=8)
    result = PolicyNoiseRobustnessRunner().run(cases)

    assert len(cases) == 40
    assert all(case.source == "toolsandbox_policy_subset" for case in cases)
    assert len(result.results) == 160
