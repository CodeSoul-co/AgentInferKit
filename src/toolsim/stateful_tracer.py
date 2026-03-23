from __future__ import annotations

from typing import List

from toolsim.stateful_executor import ExecutionRecord


class TraceRecorder:
    """Append-only recorder for stateful execution records."""

    def __init__(self) -> None:
        self._records: List[ExecutionRecord] = []

    def log(self, record: ExecutionRecord) -> None:
        self._records.append(record)

    def get_records(self) -> List[ExecutionRecord]:
        return list(self._records)

    def filter_by_status(self, status: str) -> List[ExecutionRecord]:
        return [record for record in self._records if record.status == status]

    def filter_by_tool(self, tool_name: str) -> List[ExecutionRecord]:
        return [record for record in self._records if record.tool_name == tool_name]

    def summary(self) -> dict:
        return {
            "total_calls": len(self._records),
            "successful_calls": sum(1 for record in self._records if record.success),
            "failed_calls": sum(1 for record in self._records if not record.success),
            "partial_calls": sum(1 for record in self._records if record.partial),
            "pending_calls": sum(1 for record in self._records if record.async_pending),
            "unique_tools": list(dict.fromkeys(record.tool_name for record in self._records)),
        }

    def clear(self) -> None:
        self._records.clear()

    def to_dict_list(self) -> list[dict]:
        return [record.to_dict() for record in self._records]
