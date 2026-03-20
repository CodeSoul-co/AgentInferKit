"""
stateful_executor.py — 最小可运行的有状态工具执行器

提供：
  - ExecutionRecord: 统一执行结果结构
  - StatefulExecutor: 基于 ToolSpec 的最小统一执行入口
  - create_default_tool_registry(): 当前原型工具集的默认注册函数
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from toolsim.file_tools import FILE_TOOLS
from toolsim.search_tools import SEARCH_TOOLS
from toolsim.tool_spec import ToolSpec
from toolsim.world_state import WorldState


@dataclass
class ExecutionRecord:
    """统一封装单次工具执行记录。"""

    tool_name: str
    args: Dict[str, Any] = field(default_factory=dict)
    success: bool = False
    observation: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    state_changed: bool = False
    pre_state_hash: str = ""
    post_state_hash: str = ""
    hash_changed: bool = False
    consistency_warning: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "args": self.args,
            "success": self.success,
            "observation": self.observation,
            "error": self.error,
            "state_changed": self.state_changed,
            "pre_state_hash": self.pre_state_hash,
            "post_state_hash": self.post_state_hash,
            "hash_changed": self.hash_changed,
            "consistency_warning": self.consistency_warning,
        }


class StatefulExecutor:
    """最小 stateful executor：按 tool_name 查表并执行 ToolSpec。"""

    def __init__(self, tools: Dict[str, ToolSpec], tracer: Optional[object] = None) -> None:
        self._tools = dict(tools)
        self._tracer = tracer

    def execute(self, tool_name: str, state: WorldState, args: Dict[str, Any]) -> ExecutionRecord:
        pre_state_hash = state.compute_hash()
        tool = self._tools.get(tool_name)

        if tool is None:
            record = ExecutionRecord(
                tool_name=tool_name,
                args=dict(args),
                success=False,
                observation={},
                error=f"Tool not found: {tool_name!r}",
                state_changed=False,
                pre_state_hash=pre_state_hash,
                post_state_hash=pre_state_hash,
                hash_changed=False,
            )
            self._log_record(record)
            return record

        try:
            result = tool.execute(state, args)
        except Exception as exc:
            post_state_hash = state.compute_hash()
            record = ExecutionRecord(
                tool_name=tool_name,
                args=dict(args),
                success=False,
                observation={},
                error=f"Tool execution raised an exception: {exc}",
                state_changed=False,
                pre_state_hash=pre_state_hash,
                post_state_hash=post_state_hash,
                hash_changed=(pre_state_hash != post_state_hash),
                consistency_warning=(
                    "Tool raised an exception after mutating state."
                    if pre_state_hash != post_state_hash
                    else None
                ),
            )
            self._log_record(record)
            return record

        post_state_hash = state.compute_hash()
        hash_changed = pre_state_hash != post_state_hash

        record = ExecutionRecord(
            tool_name=tool_name,
            args=dict(args),
            success=result.success,
            observation=result.observation,
            error=result.error,
            state_changed=result.state_changed,
            pre_state_hash=pre_state_hash,
            post_state_hash=post_state_hash,
            hash_changed=hash_changed,
            consistency_warning=_build_consistency_warning(result.state_changed, hash_changed),
        )
        self._log_record(record)
        return record

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

    def _log_record(self, record: ExecutionRecord) -> None:
        if self._tracer is not None:
            self._tracer.log(record)


def create_default_tool_registry() -> Dict[str, ToolSpec]:
    """构建当前最小原型的默认工具注册表。"""
    registry: Dict[str, ToolSpec] = {}
    registry.update(FILE_TOOLS)
    registry.update(SEARCH_TOOLS)
    return registry


def _build_consistency_warning(state_changed: bool, hash_changed: bool) -> Optional[str]:
    if not state_changed and hash_changed:
        return "Tool reported state_changed=False, but state hash changed."
    if state_changed and not hash_changed:
        return "Tool reported state_changed=True, but state hash did not change."
    return None
