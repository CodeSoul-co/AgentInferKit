from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from toolsim.world_state import PendingEffect, WorldState


class BaseBackend(ABC):
    """Abstract backend interface for stateful tool environments."""

    @abstractmethod
    def get_backend_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def create_state(self) -> WorldState:
        raise NotImplementedError

    @abstractmethod
    def clone_state(self, state: WorldState) -> WorldState:
        raise NotImplementedError

    @abstractmethod
    def snapshot_state(self, state: WorldState, label: Optional[str] = None) -> str:
        raise NotImplementedError

    @abstractmethod
    def rollback_state(self, state: WorldState, snapshot_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_entity(self, state: WorldState, entity_type: str, entity_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def set_entity(self, state: WorldState, entity_type: str, entity_id: str, value: Dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete_entity(self, state: WorldState, entity_type: str, entity_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def list_entities(self, state: WorldState, entity_type: str) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def schedule_effect(self, state: WorldState, effect: PendingEffect) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_pending_effects(self, state: WorldState, status: Optional[str] = None) -> List[PendingEffect]:
        raise NotImplementedError
