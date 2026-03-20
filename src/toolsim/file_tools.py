"""
file_tools.py — file 域有状态工具

实现两个最小工具：
  - FileWriteTool  (tool_name = "file.write")
  - FileReadTool   (tool_name = "file.read")

文件实体在 WorldState.entities["file"][file_id] 中存储，结构约定：

    {
        "content":    str,          # 文件正文
        "metadata":   dict,         # 调用方附加的元信息（可为空 dict）
        "created_at": float,        # 首次写入时的 state.clock
        "updated_at": float,        # 最近一次写入时的 state.clock
        "revision":   int,          # 从 1 开始，每次覆盖写入 +1
    }

设计约定：
  - file.write  会原地修改 WorldState，state_changed=True
  - file.read   纯读取，永远不修改 WorldState，state_changed=False
  - 两个工具均不依赖 registry / executor / tracer，可独立使用
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from toolsim.tool_spec import ToolExecutionResult, ToolSpec
from toolsim.world_state import WorldState

# WorldState 中存储 file 实体的顶层类型键
_FILE_ENTITY_TYPE = "file"


# ------------------------------------------------------------------
# file.write
# ------------------------------------------------------------------

class FileWriteTool(ToolSpec):
    """将内容写入 WorldState 中的虚拟文件。

    若文件不存在则创建；若文件已存在则覆盖 content 并令 revision +1。
    使用 state.clock 记录时间戳（调用方可在调用前更新 clock）。
    """

    tool_name: str = "file.write"
    description: str = (
        "Write or overwrite a virtual file in the world state. "
        "Creates the file if it does not exist."
    )
    input_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "file_id":  {"type": "string", "description": "Unique file identifier."},
            "content":  {"type": "string", "description": "Text content to write."},
            "metadata": {"type": "object", "description": "Optional metadata dict."},
        },
        "required": ["file_id", "content"],
    }

    def execute(self, state: WorldState, args: Dict[str, Any]) -> ToolExecutionResult:
        """Write content to a file entity in WorldState.

        Args:
            state: World state (modified in-place).
            args:  Must contain "file_id" and "content"; "metadata" is optional.

        Returns:
            ToolExecutionResult with state_changed=True on success.
        """
        file_id: Optional[str] = args.get("file_id")
        content: Optional[str] = args.get("content")

        if not file_id:
            return ToolExecutionResult(
                success=False,
                error="Missing required argument: file_id",
            )
        if content is None:
            return ToolExecutionResult(
                success=False,
                error="Missing required argument: content",
            )

        metadata: Dict[str, Any] = args.get("metadata") or {}
        now: float = state.clock

        existing = state.get_entity(_FILE_ENTITY_TYPE, file_id)

        if existing is None:
            # 首次创建
            entity: Dict[str, Any] = {
                "content":    content,
                "metadata":   metadata,
                "created_at": now,
                "updated_at": now,
                "revision":   1,
            }
            action = "created"
        else:
            # 覆盖写入
            entity = {
                "content":    content,
                "metadata":   metadata if metadata else existing.get("metadata", {}),
                "created_at": existing.get("created_at", now),
                "updated_at": now,
                "revision":   existing.get("revision", 0) + 1,
            }
            action = "overwritten"

        # set_entity 会自动令 state.version +1
        state.set_entity(_FILE_ENTITY_TYPE, file_id, entity)

        return ToolExecutionResult(
            success=True,
            observation={
                "tool_name": self.tool_name,
                "file_id":   file_id,
                "action":    action,
                "revision":  entity["revision"],
                "updated_at": entity["updated_at"],
            },
            state_changed=True,
        )


# ------------------------------------------------------------------
# file.read
# ------------------------------------------------------------------

class FileReadTool(ToolSpec):
    """从 WorldState 中读取虚拟文件内容。

    纯读取操作，不修改 WorldState。
    若文件不存在，返回 success=False 并附带明确错误信息。
    """

    tool_name: str = "file.read"
    description: str = (
        "Read the content of a virtual file from the world state. "
        "Returns an error if the file does not exist."
    )
    input_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "file_id": {"type": "string", "description": "Unique file identifier."},
        },
        "required": ["file_id"],
    }

    def execute(self, state: WorldState, args: Dict[str, Any]) -> ToolExecutionResult:
        """Read a file entity from WorldState.

        Args:
            state: World state (never modified).
            args:  Must contain "file_id".

        Returns:
            ToolExecutionResult with state_changed=False in all cases.
        """
        file_id: Optional[str] = args.get("file_id")

        if not file_id:
            return ToolExecutionResult(
                success=False,
                error="Missing required argument: file_id",
                state_changed=False,
            )

        entity = state.get_entity(_FILE_ENTITY_TYPE, file_id)

        if entity is None:
            return ToolExecutionResult(
                success=False,
                error=f"File not found: {file_id!r}",
                state_changed=False,
            )

        return ToolExecutionResult(
            success=True,
            observation={
                "tool_name":  self.tool_name,
                "file_id":    file_id,
                "content":    entity.get("content", ""),
                "metadata":   entity.get("metadata", {}),
                "revision":   entity.get("revision", 1),
                "created_at": entity.get("created_at"),
                "updated_at": entity.get("updated_at"),
            },
            state_changed=False,
        )


# ------------------------------------------------------------------
# 便捷注册表（供后续 executor 接入用，当前阶段仅做索引）
# ------------------------------------------------------------------

#: file 域所有工具实例，key 为 tool_name
FILE_TOOLS: Dict[str, ToolSpec] = {
    tool.tool_name: tool
    for tool in [FileWriteTool(), FileReadTool()]
}
