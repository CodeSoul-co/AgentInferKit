from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from toolsim.backends.base import BaseBackend
from toolsim.core.trace_state import PendingEffect, TraceState
from toolsim.tools.apibank_runtime import (
    APIBANK_RUNTIME_NAME,
    call_apibank_api,
    ensure_apibank_state,
    persist_apibank_databases,
)
from toolsim.tools.toolsandbox_runtime import (
    TOOLSANDBOX_RUNTIME_NAME,
    call_toolsandbox_tool,
    ensure_toolsandbox_state,
    persist_toolsandbox_databases,
    record_end_conversation,
)


class SandboxBackend(BaseBackend):
    """Isolated backend with explicit session identity for sandboxed runs."""

    def __init__(self, session_id: Optional[str] = None, artifact_root: str | Path | None = None) -> None:
        self.session_id = session_id or f"sandbox_{uuid.uuid4().hex[:8]}"
        self.artifact_root = Path(artifact_root) if artifact_root is not None else Path("tmp") / "toolsim_sandbox"
        self.session_root = self.artifact_root / _safe_name(self.session_id)
        self.files_root = self.session_root / "files"
        self.index_root = self.session_root / "search_index"

    def get_backend_name(self) -> str:
        return "sandbox"

    def create_state(self) -> TraceState:
        state = TraceState(resources={"sandbox_session": self.session_id})
        state.policies.setdefault("sandbox", {})
        state.policies["sandbox"]["session_id"] = self.session_id
        state.policies["sandbox"]["artifact_root"] = str(self.session_root)
        state.policies.setdefault("backend", {})
        state.policies["backend"]["realism"] = "sandbox_strict"
        return state

    def clone_state(self, state: TraceState) -> TraceState:
        cloned = TraceState.from_dict(state.to_dict())
        cloned.resources["sandbox_session"] = self.session_id
        cloned.policies.setdefault("sandbox", {})
        cloned.policies["sandbox"]["session_id"] = self.session_id
        cloned.policies["sandbox"]["artifact_root"] = str(self.session_root)
        cloned.policies.setdefault("backend", {})
        cloned.policies["backend"].setdefault("realism", "sandbox_strict")
        return cloned

    def snapshot_state(self, state: TraceState, label: Optional[str] = None) -> str:
        return state.create_snapshot(label or self.session_id)

    def rollback_state(self, state: TraceState, snapshot_id: str) -> bool:
        rolled_back = state.rollback_to(snapshot_id)
        if rolled_back:
            state.resources["sandbox_session"] = self.session_id
            state.policies.setdefault("sandbox", {})
            state.policies["sandbox"]["session_id"] = self.session_id
            state.policies["sandbox"]["artifact_root"] = str(self.session_root)
            state.policies.setdefault("backend", {})
            state.policies["backend"].setdefault("realism", "sandbox_strict")
        return rolled_back

    def get_entity(self, state: TraceState, entity_type: str, entity_id: str) -> Optional[Dict[str, Any]]:
        return state.get_entity(entity_type, entity_id)

    def set_entity(self, state: TraceState, entity_type: str, entity_id: str, value: Dict[str, Any]) -> None:
        state.set_entity(entity_type, entity_id, value)

    def delete_entity(self, state: TraceState, entity_type: str, entity_id: str) -> bool:
        return state.delete_entity(entity_type, entity_id)

    def list_entities(self, state: TraceState, entity_type: str) -> List[Dict[str, Any]]:
        return list(state.entities.get(entity_type, {}).values())

    def schedule_effect(self, state: TraceState, effect: PendingEffect) -> None:
        state.schedule_effect(effect)

    def list_pending_effects(self, state: TraceState, status: Optional[str] = None) -> List[PendingEffect]:
        return state.list_pending_effects(status=status)

    def ensure_apibank_account_state(self, state: TraceState) -> None:
        """Seed API-Bank databases for deterministic strict sandbox calls."""
        ensure_apibank_state(state)
        state.resources.setdefault("api_bank_session", self.session_id)
        state.policies.setdefault("backend", {})
        state.policies["backend"]["api_bank_runtime"] = APIBANK_RUNTIME_NAME
        self._persist_account_database(state)

    def call_apibank_api(self, state: TraceState, api_name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Run API-Bank APIs with strict deterministic semantics."""
        self.ensure_apibank_account_state(state)
        result = call_apibank_api(state, api_name, args)
        self._persist_account_database(state)
        return result

    def ensure_toolsandbox_state(self, state: TraceState) -> None:
        """Seed ToolSandbox databases for deterministic strict sandbox calls."""
        ensure_toolsandbox_state(state)
        state.resources.setdefault("toolsandbox_session", self.session_id)
        state.policies.setdefault("backend", {})
        state.policies["backend"]["toolsandbox_runtime"] = TOOLSANDBOX_RUNTIME_NAME
        self._persist_toolsandbox_database(state)

    def call_toolsandbox_tool(self, state: TraceState, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Run ToolSandbox tools with strict deterministic semantics."""
        self.ensure_toolsandbox_state(state)
        result = call_toolsandbox_tool(state, tool_name, args)
        self._persist_toolsandbox_database(state)
        return result

    def record_toolsandbox_end_conversation(self, state: TraceState, args: dict[str, Any]) -> dict[str, Any]:
        self.ensure_toolsandbox_state(state)
        result = record_end_conversation(state, args)
        self._persist_toolsandbox_database(state)
        return result

    def write_file_artifact(self, file_id: str, content: str) -> str:
        """Persist a sandbox file as a real artifact for live-ish file IO behavior."""
        self.files_root.mkdir(parents=True, exist_ok=True)
        path = Path(self.get_file_artifact_path(file_id))
        path.write_text(content, encoding="utf-8")
        return str(path)

    def read_file_artifact(self, file_id: str) -> str | None:
        path = Path(self.get_file_artifact_path(file_id))
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    def get_file_artifact_path(self, file_id: str) -> str:
        return str(self.files_root / f"{_safe_name(file_id)}.txt")

    def write_search_index_artifact(self, file_id: str, index_entry: dict[str, Any]) -> str:
        """Persist a searchable index snapshot separate from TraceState."""
        self.index_root.mkdir(parents=True, exist_ok=True)
        path = Path(self.get_search_index_artifact_path(file_id))
        path.write_text(json.dumps(index_entry, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        return str(path)

    def get_search_index_artifact_path(self, file_id: str) -> str:
        return str(self.index_root / f"{_safe_name(file_id)}.json")

    def list_search_index_artifacts(self) -> list[dict[str, Any]]:
        if not self.index_root.exists():
            return []
        entries: list[dict[str, Any]] = []
        for path in sorted(self.index_root.glob("*.json")):
            try:
                entry = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if isinstance(entry, dict):
                entry.setdefault("sandbox_index_path", str(path))
                entries.append(entry)
        return entries

    def _persist_account_database(self, state: TraceState) -> None:
        persist_apibank_databases(state, self.session_root)

    def _persist_toolsandbox_database(self, state: TraceState) -> None:
        persist_toolsandbox_databases(state, self.session_root)


def _safe_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", value)
    return cleaned.strip("._") or "artifact"
