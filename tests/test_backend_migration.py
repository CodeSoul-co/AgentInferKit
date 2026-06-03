"""Tests for Experiment 4 backend migration runner."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toolsim.runners.backend_migration import (
    BACKENDS,
    STRATEGIES,
    BackendMigrationRunner,
    build_backend_migration_cases,
    render_backend_migration_markdown,
)


def test_backend_migration_synthetic_cases_run_all_backends_and_strategies():
    cases = build_backend_migration_cases(include_toolsandbox=False)
    result = BackendMigrationRunner().run(cases)

    assert len(cases) == 5
    assert len(result.results) == len(cases) * len(BACKENDS) * len(STRATEGIES)
    assert len(result.group_metrics) == len(BACKENDS) * len(STRATEGIES)


def test_backend_migration_detects_live_like_gap_for_direct():
    cases = build_backend_migration_cases(include_toolsandbox=False)
    result = BackendMigrationRunner().run(cases)
    by_key = {
        (metric.strategy, metric.backend): metric
        for metric in result.group_metrics
    }

    assert by_key[("direct", "mock")].final_state_correctness == 1.0
    assert by_key[("direct", "live_like")].final_state_correctness == 0.0
    assert by_key[("direct", "live_like")].migration_gap == 1.0
    assert by_key[("cot", "live_like")].final_state_correctness == 0.4
    assert by_key[("react", "live_like")].final_state_correctness == 0.8
    assert by_key[("self_refine", "live_like")].final_state_correctness == 0.8


def test_backend_migration_toolsandbox_subset_and_report():
    cases = build_backend_migration_cases(include_synthetic=False, toolsandbox_limit=6)
    result = BackendMigrationRunner().run(cases)
    report = render_backend_migration_markdown(result)

    assert len(cases) == 6
    assert all(case.source == "toolsandbox_backend_subset" for case in cases)
    assert "# Backend Migration Report" in report
    assert "Migration Gap" in report
