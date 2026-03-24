"""Search indexing and query tools backed by WorldState entities."""

from __future__ import annotations

from typing import Any

from toolsim.core.constants import EntityType
from toolsim.core.tool_spec import PostconditionSpec, PreconditionSpec, ToolExecutionResult, ToolMetadata, ToolSpec
from toolsim.core.world_state import WorldState


class SearchIndexTool(ToolSpec):
    """Explicitly index a file snapshot in WorldState so it becomes searchable."""

    tool_name: str = "search.index"
    description: str = (
        "Explicitly index a file from the world state so it becomes searchable. "
        "The index stores a content snapshot and does not auto-refresh after file writes "
        "unless delayed effects are scheduled."
    )
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {"file_id": {"type": "string", "description": "Unique file identifier."}},
        "required": ["file_id"],
    }
    metadata = ToolMetadata(
        name="search.index",
        version="0.2",
        domain="search",
        description=description,
        input_schema=input_schema,
        required_permissions=["search.index"],
        idempotency="conditionally_idempotent",
    )
    preconditions = [
        PreconditionSpec(
            kind="entity_exists",
            message="Source file must exist before indexing",
            config={"entity_type": EntityType.FILE, "arg_field": "file_id"},
        )
    ]
    postconditions = [
        PostconditionSpec(
            kind="entity_exists",
            message="Search index entry should exist after indexing",
            config={"entity_type": EntityType.SEARCH_INDEX, "arg_field": "file_id"},
        ),
        PostconditionSpec(kind="state_hash_changed", message="World state hash should change after search.index"),
    ]

    def execute(self, state: WorldState, args: dict[str, Any]) -> ToolExecutionResult:
        file_id: str | None = args.get("file_id")
        if not file_id:
            return ToolExecutionResult(success=False, error="Missing required argument: file_id", state_changed=False)
        file_entity = state.get_entity(EntityType.FILE, file_id)
        if file_entity is None:
            return ToolExecutionResult(success=False, error=f"File not found for indexing: {file_id!r}", state_changed=False)
        index_entry = {
            "file_id": file_id,
            "indexed_content_snapshot": file_entity.get("content", ""),
            "metadata": file_entity.get("metadata", {}),
            "source_revision": file_entity.get("revision", 1),
            "indexed_at": state.clock,
        }
        state.set_entity(EntityType.SEARCH_INDEX, file_id, index_entry)
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
    """Search indexed file snapshots using simple substring matching."""

    tool_name: str = "search.query"
    description: str = (
        "Search indexed file snapshots using simple substring matching. "
        "Only explicitly indexed or delayed-reindexed files are searchable."
    )
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {"query": {"type": "string", "description": "Substring to search for."}},
        "required": ["query"],
    }
    metadata = ToolMetadata(
        name="search.query",
        version="0.1",
        domain="search",
        description=description,
        input_schema=input_schema,
        required_permissions=["search.query"],
        idempotency="idempotent",
    )

    def execute(self, state: WorldState, args: dict[str, Any]) -> ToolExecutionResult:
        query: str | None = args.get("query")
        if not query:
            return ToolExecutionResult(success=False, error="Missing required argument: query", state_changed=False)
        hits: list[dict[str, Any]] = []
        index_bucket = state.entities.get(EntityType.SEARCH_INDEX, {})
        for file_id, index_entry in index_bucket.items():
            indexed_content = index_entry.get("indexed_content_snapshot", "")
            if query in indexed_content:
                hits.append({"file_id": file_id, "content": indexed_content, "metadata": index_entry.get("metadata", {})})
        return ToolExecutionResult(
            success=True,
            observation={"tool_name": self.tool_name, "query": query, "hits": hits},
            state_changed=False,
        )


SEARCH_TOOLS: dict[str, ToolSpec] = {tool.tool_name: tool for tool in [SearchIndexTool(), SearchQueryTool()]}
