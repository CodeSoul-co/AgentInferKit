"""Reporting and aggregation for toolsim experiment results."""

from __future__ import annotations

from toolsim.reporting.reporting import (
    BatchComparisonResult,
    BatchComparisonRunner,
    CaseComparisonSummary,
    render_markdown_report,
    summarize_comparison_result,
)

__all__ = [
    "BatchComparisonRunner",
    "BatchComparisonResult",
    "CaseComparisonSummary",
    "render_markdown_report",
    "summarize_comparison_result",
]
