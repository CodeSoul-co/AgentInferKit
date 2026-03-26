"""Append-only trace recorder for stateful execution records."""

from __future__ import annotations

from typing import Any

from toolsim.execution.stateful_executor import ExecutionRecord


class TraceRecorder:
    """Append-only recorder for stateful execution records.

    Provides filtering, aggregation, and serialisation of execution traces
    produced by :class:`StatefulExecutor`.
    """

    def __init__(self) -> None:
        self._records: list[ExecutionRecord] = []

    def log(self, record: ExecutionRecord) -> None:
        """Append a single execution record."""
        self._records.append(record)

    def get_records(self) -> list[ExecutionRecord]:
        """Return a copy of all recorded execution records."""
        return list(self._records)

    def filter_by_status(self, status: str) -> list[ExecutionRecord]:
        """Return records with the given execution status (accepts enum value or raw string)."""
        return [record for record in self._records if getattr(record.status, "value", record.status) == status]

    def filter_by_tool(self, tool_name: str) -> list[ExecutionRecord]:
        """Return records for the given tool name."""
        return [record for record in self._records if record.tool_name == tool_name]

    def summary(self) -> dict[str, Any]:
        """Return an aggregate summary of all recorded calls.

        Returns:
            A dict with keys: total_calls, successful_calls, failed_calls,
            partial_calls, pending_calls, unique_tools.
        """
        return {
            "total_calls": len(self._records),
            "successful_calls": sum(1 for record in self._records if record.success),
            "failed_calls": sum(1 for record in self._records if not record.success),
            "partial_calls": sum(1 for record in self._records if record.partial),
            "pending_calls": sum(1 for record in self._records if record.async_pending),
            "unique_tools": list(dict.fromkeys(record.tool_name for record in self._records)),
        }

    def clear(self) -> None:
        """Remove all recorded execution records."""
        self._records.clear()

    def to_dict_list(self) -> list[dict[str, Any]]:
        """Return a serialised list of all execution records."""
        return [record.to_dict() for record in self._records]
