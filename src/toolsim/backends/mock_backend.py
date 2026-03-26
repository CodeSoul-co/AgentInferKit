"""In-memory backend that delegates directly to WorldState."""

from __future__ import annotations

from toolsim.backends.base import BaseBackend
from toolsim.core.constants import EffectStatus
from toolsim.core.world_state import PendingEffect, WorldState


class MockBackend(BaseBackend):
    """In-memory backend that delegates directly to WorldState."""

    def get_backend_name(self) -> str:
        return "mock"

    def create_state(self) -> WorldState:
        return WorldState()

    def clone_state(self, state: WorldState) -> WorldState:
        return WorldState.from_dict(state.to_dict())

    def snapshot_state(self, state: WorldState, label: str | None = None) -> str:
        return state.create_snapshot(label)

    def rollback_state(self, state: WorldState, snapshot_id: str) -> bool:
        return state.rollback_to(snapshot_id)

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
