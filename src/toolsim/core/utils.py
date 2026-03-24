"""Shared utility functions for toolsim evaluators and reporters."""

from __future__ import annotations

from typing import Any

from toolsim.execution.stateful_executor import ExecutionRecord


def extract_last_query_hits(trace: list[ExecutionRecord]) -> list[dict[str, Any]]:
    """Return the hits list from the last search.query record in the trace, or [].

    Args:
        trace: List of execution records from a tool call sequence.

    Returns:
        The observation["hits"] list from the final search.query call, or [] if none.
    """
    for record in reversed(trace):
        if record.tool_name == "search.query":
            return record.observation.get("hits", [])
    return []
