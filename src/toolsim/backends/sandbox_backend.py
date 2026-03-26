"""Isolated backend with explicit session identity for sandboxed runs."""

from __future__ import annotations

import uuid
from typing import Any

from toolsim.backends.base import BaseBackend
from toolsim.core.constants import EffectStatus
from toolsim.core.world_state import PendingEffect, WorldState


class SandboxBackend(BaseBackend):
    """Isolated backend with explicit session identity for sandboxed runs."""

    def __init__(self, session_id: Optional[str] = None) -> None:
        self.session_id = session_id or f"sandbox_{uuid.uuid4().hex[:8]}"

    def get_backend_name(self) -> str:
        return "sandbox"

    def create_state(self) -> WorldState:
        state = WorldState(resources={"sandbox_session": self.session_id})
        state.policies.setdefault("sandbox", {})
        state.policies["sandbox"]["session_id"] = self.session_id
        return state

    def clone_state(self, state: WorldState) -> WorldState:
        cloned = WorldState.from_dict(state.to_dict())
        cloned.resources["sandbox_session"] = self.session_id
        cloned.policies.setdefault("sandbox", {})
        cloned.policies["sandbox"]["session_id"] = self.session_id
        return cloned

    def snapshot_state(self, state: WorldState, label: str | None = None) -> str:
        return state.create_snapshot(label or self.session_id)

    def rollback_state(self, state: WorldState, snapshot_id: str) -> bool:
        rolled_back = state.rollback_to(snapshot_id)
        if rolled_back:
            state.resources["sandbox_session"] = self.session_id
            state.policies.setdefault("sandbox", {})
            state.policies["sandbox"]["session_id"] = self.session_id
        return rolled_back

    def get_entity(self, state: WorldState, entity_type: str, entity_id: str) -> dict[str, Any] | None:
        return state.get_entity(entity_type, entity_id)

    def set_entity(self, state: WorldState, entity_type: str, entity_id: str, value: dict[str, Any]) -> None:
        state.set_entity(entity_type, entity_id, value)

    def delete_entity(self, state: WorldState, entity_type: str, entity_id: str) -> bool:
        return state.delete_entity(entity_type, entity_id)

    def list_entities(self, state: WorldState, entity_type: str) -> list[dict[str, Any]]:
        return list(state.entities.get(entity_type, {}).values())

    def schedule_effect(self, state: WorldState, effect: PendingEffect) -> None:
        state.schedule_effect(effect)

    def list_pending_effects(self, state: WorldState, status: EffectStatus | None = None) -> list[PendingEffect]:
        return state.list_pending_effects(status=status)
