"""
stateful_tracer.py — 最小可运行的 execution trace recorder

复用 ExecutionRecord 作为 trace entry，维护一条顺序执行日志。
"""

from __future__ import annotations

from typing import List

from toolsim.stateful_executor import ExecutionRecord


class TraceRecorder:
    """记录按顺序发生的 ExecutionRecord。"""

    def __init__(self) -> None:
        self._records: List[ExecutionRecord] = []

    def log(self, record: ExecutionRecord) -> None:
        """追加一条执行记录。"""
        self._records.append(record)

    def get_records(self) -> List[ExecutionRecord]:
        """返回当前所有记录的浅拷贝列表。"""
        return list(self._records)

    def clear(self) -> None:
        """清空执行记录。"""
        self._records.clear()

    def to_dict_list(self) -> list[dict]:
        """导出为可序列化的字典列表。"""
        return [record.to_dict() for record in self._records]
