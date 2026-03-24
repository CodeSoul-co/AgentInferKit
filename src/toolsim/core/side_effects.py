from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from toolsim.core.constants import EFFECT_KIND_REINDEX_FILE_SNAPSHOT, EntityType, EffectStatus
from toolsim.core.world_state import PendingEffect, WorldState


@dataclass
class EffectApplicationResult:
    effect_id: str
    kind: str
    applied: bool
    error: str | None = None
    state_changed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "effect_id": self.effect_id,
            "kind": self.kind,
            "applied": self.applied,
            "error": self.error,
            "state_changed": self.state_changed,
        }


def _reindex_file_snapshot(state: WorldState, effect: PendingEffect) -> bool:
    file_id = effect.payload.get("file_id")
    if not file_id:
        raise ValueError("Missing file_id in effect payload")
    file_entity = state.get_entity(EntityType.FILE, file_id)
    if file_entity is None:
        raise ValueError(f"File not found for delayed reindex: {file_id!r}")

    index_entry = {
        "file_id": file_id,
        "indexed_content_snapshot": file_entity.get("content", ""),
        "metadata": file_entity.get("metadata", {}),
        "source_revision": file_entity.get("revision", 1),
        "indexed_at": state.now(),
    }
    state.set_entity(EntityType.SEARCH_INDEX, file_id, index_entry)
    return True


class SideEffectScheduler:
    """Apply pending effects once they become ready."""

    def __init__(self, handlers: dict[str, Callable[[WorldState, PendingEffect], bool]] | None = None) -> None:
        self._handlers: dict[str, Callable[[WorldState, PendingEffect], bool]] = dict(handlers or {})

    def register_handler(self, kind: str, handler: Callable[[WorldState, PendingEffect], bool]) -> None:
        self._handlers[kind] = handler

    def is_ready(self, effect: PendingEffect, state: WorldState) -> bool:
        return effect.status == EffectStatus.PENDING and state.now() >= effect.execute_after

    def apply_effect(self, effect: PendingEffect, state: WorldState) -> EffectApplicationResult:
        handler = self._handlers.get(effect.kind)
        if handler is None:
            state.update_pending_effect(effect.effect_id, status="failed", last_error=f"No handler registered for effect kind: {effect.kind}")
            return EffectApplicationResult(effect_id=effect.effect_id, kind=effect.kind, applied=False, error=f"No handler registered for effect kind: {effect.kind}")

        try:
            state_changed = bool(handler(state, effect))
            state.update_pending_effect(effect.effect_id, status="applied", last_error=None)
            return EffectApplicationResult(effect_id=effect.effect_id, kind=effect.kind, applied=True, state_changed=state_changed)
        except Exception as exc:
            current = state.get_pending_effect(effect.effect_id)
            retry_count = (current.retry_count if current else effect.retry_count) + 1
            new_status = "failed"
            max_retries = current.max_retries if current else effect.max_retries
            if retry_count <= max_retries:
                new_status = "pending"
            state.update_pending_effect(effect.effect_id, status=new_status, retry_count=retry_count, last_error=str(exc))
            return EffectApplicationResult(effect_id=effect.effect_id, kind=effect.kind, applied=False, error=str(exc))

    def apply_ready_effects(self, state: WorldState) -> list[EffectApplicationResult]:
        results: list[EffectApplicationResult] = []
        for effect in state.list_pending_effects(status="pending"):
            if self.is_ready(effect, state):
                results.append(self.apply_effect(effect, state))
        return results


def create_default_scheduler() -> SideEffectScheduler:
    scheduler = SideEffectScheduler()
    scheduler.register_handler(EFFECT_KIND_REINDEX_FILE_SNAPSHOT, _reindex_file_snapshot)
    return scheduler
