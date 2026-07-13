"""Helpers for small synthetic ToolSandbox fixtures used in tests."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from pathlib import Path

from toolsim.core.trace_state import TraceState


FIXTURES_DIR = Path(__file__).parent / "fixtures"
TOOLSANDBOX_JSON_PATH = FIXTURES_DIR / "toolsandbox_scenarios.json"
TOOLSANDBOX_CSV_PATH = FIXTURES_DIR / "toolsandbox_scenarios.csv"


def clone_toolsandbox_case(case, suffix: str, *, domain: str | None = None, categories: list[str] | None = None):
    return replace(
        case,
        scenario_name=f"{case.scenario_name}_{suffix}",
        domain=domain or case.domain,
        categories=list(categories or case.categories),
        required_tools=list(case.required_tools),
        initial_state=TraceState.from_dict(case.initial_state.to_dict()),
        oracle_tool_calls=deepcopy(case.oracle_tool_calls),
        goals=deepcopy(case.goals),
        minefield_goals=deepcopy(case.minefield_goals),
        metadata={**case.metadata, "fixture_clone": suffix},
    )


def expand_cases_per_domain(cases, *, per_domain: int):
    result = []
    by_domain = {}
    for case in cases:
        by_domain.setdefault(case.domain, case)
    for domain, case in sorted(by_domain.items()):
        for index in range(per_domain):
            result.append(clone_toolsandbox_case(case, f"{domain}_{index}"))
    return result


def expand_cases_by_level(cases_by_level: dict[str, object], *, per_level: int):
    result = []
    for level, case in cases_by_level.items():
        for index in range(per_level):
            result.append(clone_toolsandbox_case(case, f"{level}_{index}"))
    return result
