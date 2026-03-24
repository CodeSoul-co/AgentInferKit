"""File read/write tools backed by WorldState entities."""

from __future__ import annotations

from typing import Any

from toolsim.core.constants import DEFAULT_REINDEX_DELAY, EFFECT_KIND_REINDEX_FILE_SNAPSHOT, EntityType
from toolsim.core.tool_spec import PostconditionSpec, PreconditionSpec, ToolExecutionResult, ToolMetadata, ToolSpec
from toolsim.core.world_state import WorldState


class FileWriteTool(ToolSpec):
    """Write or overwrite a file entity inside WorldState."""

    tool_name: str = "file.write"
    description: str = (
        "Write or overwrite a virtual file in the world state. "
        "Creates the file if it does not exist."
    )
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "file_id": {"type": "string", "description": "Unique file identifier."},
            "content": {"type": "string", "description": "Text content to write."},
            "metadata": {"type": "object", "description": "Optional metadata dict."},
            "schedule_search_reindex": {"type": "boolean", "description": "Whether to schedule delayed reindexing."},
            "reindex_delay": {"type": "number", "description": "Delay before delayed reindex effect becomes ready."},
        },
        "required": ["file_id", "content"],
    }
    metadata = ToolMetadata(
        name="file.write",
        version="0.2",
        domain="file",
        description=description,
        input_schema=input_schema,
        required_permissions=["file.write"],
        idempotency="conditionally_idempotent",
    )
    postconditions = [
        PostconditionSpec(
            kind="entity_exists",
            message="File entity should exist after write",
            config={"entity_type": EntityType.FILE, "arg_field": "file_id"},
        ),
        PostconditionSpec(kind="state_hash_changed", message="World state hash should change after file.write"),
    ]

    def execute(self, state_or_context: Any, args: dict[str, Any]) -> ToolExecutionResult:
        state = self.get_state_from_input(state_or_context)
        clock = state_or_context.now() if hasattr(state_or_context, "now") else state.clock
        file_id: str | None = args.get("file_id")
        content: str | None = args.get("content")

        if not file_id:
            return ToolExecutionResult(success=False, error="Missing required argument: file_id")
        if content is None:
            return ToolExecutionResult(success=False, error="Missing required argument: content")

        metadata: dict[str, Any] = args.get("metadata") or {}
        existing = state.get_entity(EntityType.FILE, file_id)

        if existing is None:
            entity: dict[str, Any] = {
                "content": content,
                "metadata": metadata,
                "created_at": clock,
                "updated_at": clock,
                "revision": 1,
            }
            action = "created"
        else:
            entity = {
                "content": content,
                "metadata": metadata if metadata else existing.get("metadata", {}),
                "created_at": existing.get("created_at", clock),
                "updated_at": clock,
                "revision": existing.get("revision", 0) + 1,
            }
            action = "overwritten"

        state.set_entity(EntityType.FILE, file_id, entity)

        scheduled_effects = []
        if args.get("schedule_search_reindex"):
            delay = float(args.get("reindex_delay", DEFAULT_REINDEX_DELAY))
            scheduled_effects.append({
                "effect_id": f"eff_reindex_{file_id}_{entity['revision']}",
                "kind": EFFECT_KIND_REINDEX_FILE_SNAPSHOT,
                "scheduled_at": clock,
                "execute_after": clock + delay,
                "payload": {"file_id": file_id},
                "status": "pending",
                "source_tool": self.tool_name,
            })

        return ToolExecutionResult(
            success=True,
            observation={
                "tool_name": self.tool_name,
                "file_id": file_id,
                "action": action,
                "revision": entity["revision"],
                "updated_at": entity["updated_at"],
            },
            state_changed=True,
            pending=bool(scheduled_effects),
            scheduled_effects=scheduled_effects,
        )


class FileReadTool(ToolSpec):
    """Read a file entity from WorldState without mutating it."""

    tool_name: str = "file.read"
    description: str = (
        "Read the content of a virtual file from the world state. "
        "Returns an error if the file does not exist."
    )
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {"file_id": {"type": "string", "description": "Unique file identifier."}},
        "required": ["file_id"],
    }
    metadata = ToolMetadata(
        name="file.read",
        version="0.1",
        domain="file",
        description=description,
        input_schema=input_schema,
        required_permissions=["file.read"],
        idempotency="idempotent",
    )
    preconditions = [
        PreconditionSpec(
            kind="entity_exists",
            message="File must exist before read",
            config={"entity_type": EntityType.FILE, "arg_field": "file_id"},
        )
    ]

    def execute(self, state: WorldState, args: dict[str, Any]) -> ToolExecutionResult:
        file_id: str | None = args.get("file_id")
        if not file_id:
            return ToolExecutionResult(success=False, error="Missing required argument: file_id", state_changed=False)
        entity = state.get_entity(EntityType.FILE, file_id)
        if entity is None:
            return ToolExecutionResult(success=False, error=f"File not found: {file_id!r}", state_changed=False)
        return ToolExecutionResult(
            success=True,
            observation={
                "tool_name": self.tool_name,
                "file_id": file_id,
                "content": entity.get("content", ""),
                "metadata": entity.get("metadata", {}),
                "revision": entity.get("revision", 1),
                "created_at": entity.get("created_at"),
                "updated_at": entity.get("updated_at"),
            },
            state_changed=False,
        )


FILE_TOOLS: dict[str, ToolSpec] = {tool.tool_name: tool for tool in [FileWriteTool(), FileReadTool()]}
