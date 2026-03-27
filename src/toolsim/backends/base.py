"""Abstract backend interface shared by in-memory and sandboxed toolsim backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from toolsim.core.constants import EffectStatus
from toolsim.core.world_state import PendingEffect, WorldState


class BaseBackend(ABC):
    """Abstract backend interface for stateful tool environments."""

    @abstractmethod
    def get_backend_name(self) -> str:
        """Return the backend's identifier string."""

    @abstractmethod
    def create_state(self) -> WorldState:
        """Create and return a fresh WorldState."""

    @abstractmethod
    def clone_state(self, state: WorldState) -> WorldState:
        """Return a deep copy of the given WorldState."""

    @abstractmethod
    def snapshot_state(self, state: WorldState, label: str | None = None) -> str:
        """Snapshot the world state and return its snapshot_id."""

    @abstractmethod
    def rollback_state(self, state: WorldState, snapshot_id: str) -> bool:
        """Roll back the world state to the given snapshot. Returns True on success."""

    @abstractmethod
    def get_entity(self, state: WorldState, entity_type: str, entity_id: str) -> dict[str, Any] | None:
        """Get a single entity by type and id, or None if absent."""

    @abstractmethod
    def set_entity(self, state: WorldState, entity_type: str, entity_id: str, value: dict[str, Any]) -> None:
        """Set or overwrite an entity in the world state."""

    @abstractmethod
    def delete_entity(self, state: WorldState, entity_type: str, entity_id: str) -> bool:
        """Remove an entity. Returns True if it existed."""

    @abstractmethod
    def list_entities(self, state: WorldState, entity_type: str) -> list[dict[str, Any]]:
        """Return all entities of the given type."""

    @abstractmethod
    def schedule_effect(self, state: WorldState, effect: PendingEffect) -> None:
        """Schedule a pending side-effect on the world state."""

    @abstractmethod
    def list_pending_effects(self, state: WorldState, status: EffectStatus | None = None) -> list[PendingEffect]:
        """Return pending effects, optionally filtered by EffectStatus."""
