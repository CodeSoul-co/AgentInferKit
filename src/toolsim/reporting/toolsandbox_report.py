"""Markdown reports for ToolSandbox benchmark runs."""

from __future__ import annotations

from pathlib import Path

from toolsim.runners.toolsandbox_benchmark import (
    ToolSandboxBenchmarkResult,
    ToolSandboxGroupMetrics,
)


def render_toolsandbox_benchmark_markdown(
    benchmark: ToolSandboxBenchmarkResult,
    *,
    max_examples: int = 8,
) -> str:
    """Render a ToolSandbox benchmark result as Markdown."""
    metrics = benchmark.metrics
    lines = [
        "# ToolSandbox Benchmark Report",
        "",
        "## Overview",
        f"- Mode: {benchmark.mode}",
        f"- Total cases: {metrics.total_cases}",
        f"- Goal-evaluable cases: {metrics.goal_cases}",
        f"- Success rate: {_pct(metrics.success_rate)}",
        f"- Minefield cases: {metrics.minefield_cases}",
        f"- Minefield violation rate: {_pct(metrics.minefield_violation_rate)}",
        f"- State corruption rate: {_pct(metrics.state_corruption_rate)}",
        f"- Average tool calls: {metrics.average_tool_calls:.2f}",
        f"- Invalid call rate: {_pct(metrics.invalid_call_rate)}",
        "",
        "## By Domain",
        "",
        _group_table(metrics.by_domain.values()),
        "",
        "## By Category",
        "",
        _group_table(metrics.by_category.values()),
        "",
    ]

    failures = [result for result in benchmark.results if result.goal_success is False]
    violations = [result for result in benchmark.results if result.minefield_violation]

    lines.extend(["## Representative Failed Cases", ""])
    if failures:
        for result in failures[:max_examples]:
            lines.extend(_case_lines(result))
    else:
        lines.append("- No goal failures.")
        lines.append("")

    lines.extend(["## Representative Minefield Violations", ""])
    if violations:
        for result in violations[:max_examples]:
            lines.extend(_case_lines(result, include_minefields=True))
    else:
        lines.append("- No minefield violations.")
        lines.append("")

    return "\n".join(lines)


def write_toolsandbox_benchmark_markdown(
    benchmark: ToolSandboxBenchmarkResult,
    path: str | Path,
    *,
    max_examples: int = 8,
) -> Path:
    """Write a ToolSandbox benchmark report to disk."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        render_toolsandbox_benchmark_markdown(benchmark, max_examples=max_examples),
        encoding="utf-8",
    )
    return output_path


def _group_table(groups) -> str:
    ordered = sorted(groups, key=lambda item: (-item.total_cases, item.group_name))
    lines = [
        "| Group | Cases | Goal Cases | Success | Minefield Cases | Minefield Violations | Avg Tool Calls | Invalid Calls |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for group in ordered:
        lines.append(_group_row(group))
    return "\n".join(lines)


def _group_row(group: ToolSandboxGroupMetrics) -> str:
    return (
        f"| {group.group_name} | {group.total_cases} | {group.goal_cases} | "
        f"{_pct(group.success_rate)} | {group.minefield_cases} | "
        f"{_pct(group.minefield_violation_rate)} | {group.average_tool_calls:.2f} | "
        f"{group.invalid_call_count} |"
    )


def _case_lines(result, include_minefields: bool = False) -> list[str]:
    lines = [
        f"### {result.scenario_name}",
        "",
        f"- Domain: {result.domain}",
        f"- Categories: {', '.join(result.categories)}",
        f"- Goal success: {result.goal_success}",
        f"- Minefield violation: {result.minefield_violation}",
        f"- Tool calls: {result.tool_call_count}",
        f"- Sequence: {' -> '.join(record.tool_name for record in result.result.trace)}",
    ]
    if result.goal_success is False and result.result.state_metrics is not None:
        failed = [detail.message for detail in result.result.state_metrics.details if not detail.passed]
        lines.append(f"- Failed goals: {'; '.join(failed[:3])}")
    if include_minefields and result.minefield_metrics is not None:
        violated = [detail.message for detail in result.minefield_metrics.details if detail.passed]
        lines.append(f"- Violated minefields: {'; '.join(violated[:3])}")
    lines.append("")
    return lines


def _pct(value: float) -> str:
    return f"{value * 100:.1f}%"
