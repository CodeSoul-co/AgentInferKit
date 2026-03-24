"""Legacy tool call tracer for experiment runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class CallTrace:
    """Record of a single tool call."""

    tool_id: str
    parameters: dict[str, Any]
    response: dict[str, Any]
    status: str  # "success" | "error_not_found" | "error_execution"
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class ToolCallTracer:
    """Manages tool call traces for an experiment run."""

    def __init__(self) -> None:
        self._traces: list[CallTrace] = []

    def record(
        self,
        tool_id: str,
        parameters: dict[str, Any],
        response: dict[str, Any],
        status: str,
    ) -> None:
        """Record a tool call.

        Args:
            tool_id: The invoked tool's identifier.
            parameters: Parameters passed to the tool.
            response: The mock response returned.
            status: Call status string.
        """
        trace = CallTrace(
            tool_id=tool_id,
            parameters=parameters,
            response=response,
            status=status,
        )
        self._traces.append(trace)

    def get_traces(self) -> list[CallTrace]:
        """Return all recorded traces."""
        return list(self._traces)

    def clear(self) -> None:
        """Clear all traces."""
        self._traces.clear()

    def to_dicts(self) -> list[dict[str, Any]]:
        """Convert all traces to a list of plain dicts (for serialization)."""
        return [
            {
                "tool_id": t.tool_id,
                "parameters": t.parameters,
                "response": t.response,
                "status": t.status,
                "timestamp": t.timestamp,
            }
            for t in self._traces
        ]
