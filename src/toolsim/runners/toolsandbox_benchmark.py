"""Benchmark runner for converted ToolSandbox cases."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable

from toolsim.adapters.toolsandbox_adapter import ToolSandboxConvertedCase, convert_toolsandbox_file
from toolsim.evaluators.evaluator import StateEvaluationResult, StateLevelEvaluator
from toolsim.runners.experiment_runner import ExperimentResult, ExperimentRunner

ToolCallProvider = Callable[[ToolSandboxConvertedCase], list[dict[str, Any]]]


@dataclass
class ToolSandboxCaseResult:
    scenario_name: str
    domain: str
    categories: list[str]
    required_tools: list[str]
    goal_count: int
    minefield_goal_count: int
    tool_call_count: int
    invalid_call_count: int
    all_calls_succeeded: bool
    goal_success: bool | None
    minefield_violation: bool
    minefield_violation_count: int
    state_corrupted: bool
    result: ExperimentResult
    minefield_metrics: StateEvaluationResult | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_name": self.scenario_name,
            "domain": self.domain,
            "categories": self.categories,
            "required_tools": self.required_tools,
            "goal_count": self.goal_count,
            "minefield_goal_count": self.minefield_goal_count,
            "tool_call_count": self.tool_call_count,
            "invalid_call_count": self.invalid_call_count,
            "all_calls_succeeded": self.all_calls_succeeded,
            "goal_success": self.goal_success,
            "minefield_violation": self.minefield_violation,
            "minefield_violation_count": self.minefield_violation_count,
            "state_corrupted": self.state_corrupted,
            "result": self.result.to_dict(),
            "minefield_metrics": self.minefield_metrics.to_dict() if self.minefield_metrics is not None else None,
        }


@dataclass
class ToolSandboxGroupMetrics:
    group_name: str
    total_cases: int = 0
    goal_cases: int = 0
    success_count: int = 0
    minefield_cases: int = 0
    minefield_violation_count: int = 0
    total_tool_calls: int = 0
    invalid_call_count: int = 0

    @property
    def success_rate(self) -> float:
        return self.success_count / self.goal_cases if self.goal_cases else 0.0

    @property
    def minefield_violation_rate(self) -> float:
        return self.minefield_violation_count / self.minefield_cases if self.minefield_cases else 0.0

    @property
    def average_tool_calls(self) -> float:
        return self.total_tool_calls / self.total_cases if self.total_cases else 0.0

    @property
    def invalid_call_rate(self) -> float:
        return self.invalid_call_count / self.total_tool_calls if self.total_tool_calls else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "group_name": self.group_name,
            "total_cases": self.total_cases,
            "goal_cases": self.goal_cases,
            "success_count": self.success_count,
            "success_rate": self.success_rate,
            "minefield_cases": self.minefield_cases,
            "minefield_violation_count": self.minefield_violation_count,
            "minefield_violation_rate": self.minefield_violation_rate,
            "average_tool_calls": self.average_tool_calls,
            "invalid_call_count": self.invalid_call_count,
            "invalid_call_rate": self.invalid_call_rate,
        }


@dataclass
class ToolSandboxBenchmarkMetrics:
    total_cases: int
    goal_cases: int
    success_count: int
    minefield_cases: int
    minefield_violation_count: int
    state_corruption_count: int
    total_tool_calls: int
    invalid_call_count: int
    success_rate: float
    minefield_violation_rate: float
    state_corruption_rate: float
    average_tool_calls: float
    invalid_call_rate: float
    by_domain: dict[str, ToolSandboxGroupMetrics] = field(default_factory=dict)
    by_category: dict[str, ToolSandboxGroupMetrics] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_cases": self.total_cases,
            "goal_cases": self.goal_cases,
            "success_count": self.success_count,
            "minefield_cases": self.minefield_cases,
            "minefield_violation_count": self.minefield_violation_count,
            "state_corruption_count": self.state_corruption_count,
            "total_tool_calls": self.total_tool_calls,
            "invalid_call_count": self.invalid_call_count,
            "success_rate": self.success_rate,
            "minefield_violation_rate": self.minefield_violation_rate,
            "state_corruption_rate": self.state_corruption_rate,
            "average_tool_calls": self.average_tool_calls,
            "invalid_call_rate": self.invalid_call_rate,
            "by_domain": {key: value.to_dict() for key, value in self.by_domain.items()},
            "by_category": {key: value.to_dict() for key, value in self.by_category.items()},
        }


@dataclass
class ToolSandboxBenchmarkResult:
    results: list[ToolSandboxCaseResult]
    metrics: ToolSandboxBenchmarkMetrics
    mode: str = "oracle"

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "metrics": self.metrics.to_dict(),
            "results": [result.to_dict() for result in self.results],
        }


class ToolSandboxBenchmarkRunner:
    """Run ToolSandbox converted cases through the stateful experiment runner."""

    def __init__(
        self,
        experiment_runner: ExperimentRunner | None = None,
        state_evaluator: StateLevelEvaluator | None = None,
    ) -> None:
        self._experiment_runner = experiment_runner or ExperimentRunner()
        self._state_evaluator = state_evaluator or StateLevelEvaluator()

    def run_file(
        self,
        path: str,
        *,
        limit: int | None = None,
        tool_call_provider: ToolCallProvider | None = None,
        mode: str = "oracle",
    ) -> ToolSandboxBenchmarkResult:
        return self.run(
            convert_toolsandbox_file(path, limit=limit),
            tool_call_provider=tool_call_provider,
            mode=mode,
        )

    def run(
        self,
        cases: list[ToolSandboxConvertedCase],
        *,
        tool_call_provider: ToolCallProvider | None = None,
        mode: str = "oracle",
    ) -> ToolSandboxBenchmarkResult:
        results = [
            self.run_case(case, tool_call_provider=tool_call_provider)
            for case in cases
        ]
        return ToolSandboxBenchmarkResult(results=results, metrics=_compute_metrics(results), mode=mode)

    def run_case(
        self,
        case: ToolSandboxConvertedCase,
        *,
        tool_call_provider: ToolCallProvider | None = None,
    ) -> ToolSandboxCaseResult:
        tool_calls = tool_call_provider(case) if tool_call_provider is not None else case.oracle_tool_calls
        result = self._experiment_runner.run(
            tool_calls=tool_calls,
            initial_state=case.initial_state,
            goals=case.goals if case.goals else None,
        )
        minefield_metrics = (
            self._state_evaluator.evaluate(result.final_state, case.minefield_goals)
            if case.minefield_goals
            else None
        )
        minefield_violation_count = minefield_metrics.passed_count if minefield_metrics is not None else 0
        goal_success = result.state_metrics.all_passed if result.state_metrics is not None else None
        state_corrupted = goal_success is False or minefield_violation_count > 0

        return ToolSandboxCaseResult(
            scenario_name=case.scenario_name,
            domain=case.domain,
            categories=case.categories,
            required_tools=case.required_tools,
            goal_count=len(case.goals),
            minefield_goal_count=len(case.minefield_goals),
            tool_call_count=len(result.trace),
            invalid_call_count=result.call_metrics.invalid_calls,
            all_calls_succeeded=result.all_calls_succeeded,
            goal_success=goal_success,
            minefield_violation=minefield_violation_count > 0,
            minefield_violation_count=minefield_violation_count,
            state_corrupted=state_corrupted,
            result=result,
            minefield_metrics=minefield_metrics,
        )


def _compute_metrics(results: list[ToolSandboxCaseResult]) -> ToolSandboxBenchmarkMetrics:
    total_cases = len(results)
    goal_cases = sum(1 for result in results if result.goal_success is not None)
    success_count = sum(1 for result in results if result.goal_success is True)
    minefield_cases = sum(1 for result in results if result.minefield_goal_count > 0)
    minefield_violation_count = sum(1 for result in results if result.minefield_violation)
    state_corruption_count = sum(1 for result in results if result.state_corrupted)
    total_tool_calls = sum(result.tool_call_count for result in results)
    invalid_call_count = sum(result.invalid_call_count for result in results)

    by_domain = _group_metrics(results, lambda result: [result.domain or "unknown"])
    by_category = _group_metrics(results, lambda result: result.categories or ["uncategorized"])

    return ToolSandboxBenchmarkMetrics(
        total_cases=total_cases,
        goal_cases=goal_cases,
        success_count=success_count,
        minefield_cases=minefield_cases,
        minefield_violation_count=minefield_violation_count,
        state_corruption_count=state_corruption_count,
        total_tool_calls=total_tool_calls,
        invalid_call_count=invalid_call_count,
        success_rate=success_count / goal_cases if goal_cases else 0.0,
        minefield_violation_rate=minefield_violation_count / minefield_cases if minefield_cases else 0.0,
        state_corruption_rate=state_corruption_count / total_cases if total_cases else 0.0,
        average_tool_calls=total_tool_calls / total_cases if total_cases else 0.0,
        invalid_call_rate=invalid_call_count / total_tool_calls if total_tool_calls else 0.0,
        by_domain=by_domain,
        by_category=by_category,
    )


def _group_metrics(
    results: list[ToolSandboxCaseResult],
    key_fn: Callable[[ToolSandboxCaseResult], list[str]],
) -> dict[str, ToolSandboxGroupMetrics]:
    grouped: dict[str, ToolSandboxGroupMetrics] = defaultdict(lambda: ToolSandboxGroupMetrics(group_name=""))
    for result in results:
        for key in key_fn(result):
            metric = grouped[key]
            metric.group_name = key
            _add_to_group(metric, result)
    return dict(sorted(grouped.items()))


def _add_to_group(metric: ToolSandboxGroupMetrics, result: ToolSandboxCaseResult) -> None:
    metric.total_cases += 1
    metric.total_tool_calls += result.tool_call_count
    metric.invalid_call_count += result.invalid_call_count
    if result.goal_success is not None:
        metric.goal_cases += 1
    if result.goal_success is True:
        metric.success_count += 1
    if result.minefield_goal_count > 0:
        metric.minefield_cases += 1
    if result.minefield_violation:
        metric.minefield_violation_count += 1
