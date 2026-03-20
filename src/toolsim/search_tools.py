"""
search_tools.py — search 域有状态工具

实现两个最小工具：
  - SearchIndexTool  (tool_name = "search.index")
  - SearchQueryTool  (tool_name = "search.query")

索引实体存储在 WorldState.entities["search_index"][file_id] 中，结构约定：

    {
        "file_id": str,
        "indexed_content_snapshot": str,
        "metadata": dict,
        "source_revision": int,
        "indexed_at": float,
    }

设计约定：
  - search.index 会读取 WorldState.entities["file"]，并将当前文件快照写入索引
  - file.write 不会自动同步 search_index，因此索引可能滞后于文件最新内容
  - search.query 只在已索引快照中做最小 substring matching，不修改 WorldState
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from toolsim.tool_spec import ToolExecutionResult, ToolSpec
from toolsim.world_state import WorldState

_FILE_ENTITY_TYPE = "file"
_SEARCH_INDEX_ENTITY_TYPE = "search_index"


class SearchIndexTool(ToolSpec):
    """将 file 实体的当前内容快照显式加入搜索索引。"""

    tool_name: str = "search.index"
    description: str = (
        "Explicitly index a file from the world state so it becomes searchable. "
        "The index stores a content snapshot and does not auto-refresh after file writes."
    )
    input_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "file_id": {"type": "string", "description": "Unique file identifier."},
        },
        "required": ["file_id"],
    }

    def execute(self, state: WorldState, args: Dict[str, Any]) -> ToolExecutionResult:
        file_id: Optional[str] = args.get("file_id")

        if not file_id:
            return ToolExecutionResult(
                success=False,
                error="Missing required argument: file_id",
                state_changed=False,
            )

        file_entity = state.get_entity(_FILE_ENTITY_TYPE, file_id)
        if file_entity is None:
            return ToolExecutionResult(
                success=False,
                error=f"File not found for indexing: {file_id!r}",
                state_changed=False,
            )

        index_entry = {
            "file_id": file_id,
            "indexed_content_snapshot": file_entity.get("content", ""),
            "metadata": file_entity.get("metadata", {}),
            "source_revision": file_entity.get("revision", 1),
            "indexed_at": state.clock,
        }
        state.set_entity(_SEARCH_INDEX_ENTITY_TYPE, file_id, index_entry)

        return ToolExecutionResult(
            success=True,
            observation={
                "tool_name": self.tool_name,
                "file_id": file_id,
                "action": "indexed",
                "source_revision": index_entry["source_revision"],
                "indexed_at": index_entry["indexed_at"],
            },
            state_changed=True,
        )


class SearchQueryTool(ToolSpec):
    """仅在显式索引快照中进行最小 substring matching。"""

    tool_name: str = "search.query"
    description: str = (
        "Search indexed file snapshots using simple substring matching. "
        "Only explicitly indexed files are searchable."
    )
    input_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Substring to search for."},
        },
        "required": ["query"],
    }

    def execute(self, state: WorldState, args: Dict[str, Any]) -> ToolExecutionResult:
        query: Optional[str] = args.get("query")

        if not query:
            return ToolExecutionResult(
                success=False,
                error="Missing required argument: query",
                state_changed=False,
            )

        hits: List[Dict[str, Any]] = []
        index_bucket = state.entities.get(_SEARCH_INDEX_ENTITY_TYPE, {})

        for file_id, index_entry in index_bucket.items():
            indexed_content = index_entry.get("indexed_content_snapshot", "")
            if query in indexed_content:
                hits.append(
                    {
                        "file_id": file_id,
                        "content": indexed_content,
                        "metadata": index_entry.get("metadata", {}),
                    }
                )

        return ToolExecutionResult(
            success=True,
            observation={
                "tool_name": self.tool_name,
                "query": query,
                "hits": hits,
            },
            state_changed=False,
        )


SEARCH_TOOLS: Dict[str, ToolSpec] = {
    tool.tool_name: tool
    for tool in [SearchIndexTool(), SearchQueryTool()]
}
