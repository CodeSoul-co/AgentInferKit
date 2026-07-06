"""Reporting and aggregation for toolsim experiment results."""

from __future__ import annotations

from toolsim.reporting.reporting import (
    BatchComparisonResult,
    BatchComparisonRunner,
    CaseComparisonSummary,
    render_markdown_report,
    summarize_comparison_result,
)
from toolsim.reporting.fault_report import (
    render_fault_robustness_markdown,
    write_fault_robustness_markdown,
)
from toolsim.reporting.trace_report import (
    render_stateful_trace_markdown,
    write_stateful_trace_markdown,
)
from toolsim.reporting.toolsandbox_report import (
    render_toolsandbox_benchmark_markdown,
    write_toolsandbox_benchmark_markdown,
)

__all__ = [
    "BatchComparisonRunner",
    "BatchComparisonResult",
    "CaseComparisonSummary",
    "render_fault_robustness_markdown",
    "render_markdown_report",
    "render_stateful_trace_markdown",
    "render_toolsandbox_benchmark_markdown",
    "summarize_comparison_result",
    "write_fault_robustness_markdown",
    "write_stateful_trace_markdown",
    "write_toolsandbox_benchmark_markdown",
]
