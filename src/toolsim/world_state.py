from __future__ import annotations

import copy
import hashlib
import json
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PendingEffect:
    """Deferred side effect placeholder for later execution."""

    effect_id: str
    kind: str
    scheduled_at: float
    execute_after: float
    payload: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    source_tool: str = ""
    retry_count: int = 0
    max_retries: int = 0
    last_error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "effect_id": self.effect_id,
            "kind": self.kind,
            "scheduled_at": self.scheduled_at,
            "execute_after": self.execute_after,
            "payload": copy.deepcopy(self.payload),
            "status": self.status,
            "source_tool": self.source_tool,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "last_error": self.last_error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PendingEffect":
        return cls(
            effect_id=str(data.get("effect_id", "")),
            kind=str(data.get("kind", "unknown")),
            scheduled_at=float(data.get("scheduled_at", 0.0)),
            execute_after=float(data.get("execute_after", 0.0)),
            payload=copy.deepcopy(data.get("payload", {})),
            status=str(data.get("status", "pending")),
            source_tool=str(data.get("source_tool", "")),
            retry_count=int(data.get("retry_count", 0)),
            max_retries=int(data.get("max_retries", 0)),
            last_error=data.get("last_error"),
        )


@dataclass
class StateSnapshot:
    snapshot_id: str
    label: Optional[str]
    created_at: float
    state_hash: str
    payload: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "label": self.label,
            "created_at": self.created_at,
            "state_hash": self.state_hash,
            "payload": copy.deepcopy(self.payload),
        }


@dataclass
class PolicyDecision:
    allowed: bool
    reason: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"allowed": self.allowed, "reason": self.reason, "details": self.details}


class WorldState:
    """Minimal but extensible stateful world model for toolsim."""

    def __init__(
        self,
        entities: Optional[Dict[str, Dict[str, Any]]] = None,
        relations: Optional[Dict[str, Any]] = None,
        resources: Optional[Dict[str, Any]] = None,
        policies: Optional[Dict[str, Any]] = None,
        clock: float = 0.0,
        version: int = 0,
        pending_effects: Optional[List[PendingEffect | Dict[str, Any]]] = None,
    ) -> None:
        self.entities: Dict[str, Dict[str, Any]] = copy.deepcopy(entities) if entities is not None else {}
        self.relations: Dict[str, Any] = copy.deepcopy(relations) if relations is not None else {}
        self.resources: Dict[str, Any] = copy.deepcopy(resources) if resources is not None else {}
        self.policies: Dict[str, Any] = copy.deepcopy(policies) if policies is not None else {}
        self.clock: float = float(clock)
        self.version: int = int(version)
        self.pending_effects: List[PendingEffect] = [
            effect if isinstance(effect, PendingEffect) else PendingEffect.from_dict(effect)
            for effect in (pending_effects or [])
        ]
        self._snapshots: Dict[str, StateSnapshot] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entities": copy.deepcopy(self.entities),
            "relations": copy.deepcopy(self.relations),
            "resources": copy.deepcopy(self.resources),
            "policies": copy.deepcopy(self.policies),
            "clock": self.clock,
            "version": self.version,
            "pending_effects": [effect.to_dict() for effect in self.pending_effects],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorldState":
        return cls(
            entities=copy.deepcopy(data.get("entities", {})),
            relations=copy.deepcopy(data.get("relations", {})),
            resources=copy.deepcopy(data.get("resources", {})),
            policies=copy.deepcopy(data.get("policies", {})),
            clock=float(data.get("clock", 0.0)),
            version=int(data.get("version", 0)),
            pending_effects=copy.deepcopy(data.get("pending_effects", [])),
        )

    def now(self) -> float:
        return self.clock

    def set_clock(self, ts: float) -> None:
        self.clock = float(ts)
        self.version += 1

    def advance_clock(self, delta: float) -> None:
        self.clock += float(delta)
        self.version += 1

    def get_entity(self, entity_type: str, entity_id: str) -> Optional[Dict[str, Any]]:
        return self.entities.get(entity_type, {}).get(entity_id)

    def set_entity(self, entity_type: str, entity_id: str, value: Dict[str, Any]) -> None:
        if entity_type not in self.entities:
            self.entities[entity_type] = {}
        self.entities[entity_type][entity_id] = copy.deepcopy(value)
        self.version += 1

    def delete_entity(self, entity_type: str, entity_id: str) -> bool:
        bucket = self.entities.get(entity_type, {})
        if entity_id not in bucket:
            return False
        del bucket[entity_id]
        if not bucket:
            del self.entities[entity_type]
        self.version += 1
        return True

    def snapshot(self) -> Dict[str, Any]:
        return self.to_dict()

    def restore(self, snapshot: Dict[str, Any]) -> None:
        restored = WorldState.from_dict(snapshot)
        self.entities = restored.entities
        self.relations = restored.relations
        self.resources = restored.resources
        self.policies = restored.policies
        self.clock = restored.clock
        self.version = restored.version
        self.pending_effects = restored.pending_effects

    def create_snapshot(self, label: Optional[str] = None) -> str:
        snapshot_id = f"snap_{uuid.uuid4().hex[:12]}"
        payload = self.snapshot()
        self._snapshots[snapshot_id] = StateSnapshot(
            snapshot_id=snapshot_id,
            label=label,
            created_at=self.clock,
            state_hash=self.compute_hash(),
            payload=payload,
        )
        return snapshot_id

    def rollback_to(self, snapshot_id: str) -> bool:
        snapshot = self._snapshots.get(snapshot_id)
        if snapshot is None:
            return False
        self.restore(snapshot.payload)
        self.version += 1
        return True

    def list_snapshots(self) -> List[StateSnapshot]:
        return list(self._snapshots.values())

    def schedule_effect(self, effect: PendingEffect) -> None:
        self.pending_effects.append(copy.deepcopy(effect))
        self.version += 1

    def get_pending_effect(self, effect_id: str) -> Optional[PendingEffect]:
        for effect in self.pending_effects:
            if effect.effect_id == effect_id:
                return copy.deepcopy(effect)
        return None

    def update_pending_effect(self, effect_id: str, **fields: Any) -> bool:
        for effect in self.pending_effects:
            if effect.effect_id == effect_id:
                for key, value in fields.items():
                    setattr(effect, key, value)
                self.version += 1
                return True
        return False

    def remove_pending_effect(self, effect_id: str) -> bool:
        for idx, effect in enumerate(self.pending_effects):
            if effect.effect_id == effect_id:
                del self.pending_effects[idx]
                self.version += 1
                return True
        return False

    def list_pending_effects(self, status: Optional[str] = None) -> List[PendingEffect]:
        if status is None:
            return [copy.deepcopy(effect) for effect in self.pending_effects]
        return [copy.deepcopy(effect) for effect in self.pending_effects if effect.status == status]

    def check_policy(self, action: str, args: Dict[str, Any], permissions: Optional[set[str]] = None) -> PolicyDecision:
        permission_set = permissions or set()
        required_map = self.policies.get("required_permissions", {})
        blocked_actions = set(self.policies.get("blocked_actions", []))

        if action in blocked_actions:
            return PolicyDecision(allowed=False, reason=f"Action blocked by policy: {action}")

        required = required_map.get(action, [])
        missing = [perm for perm in required if perm not in permission_set]
        if missing:
            return PolicyDecision(
                allowed=False,
                reason=f"Missing policy-required permissions for {action}",
                details={"missing_permissions": missing, "args": copy.deepcopy(args)},
            )

        return PolicyDecision(allowed=True, reason="Policy check passed")

    def compute_hash(self) -> str:
        payload = self._stable_serialize()
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _stable_serialize(self) -> str:
        data = {
            "entities": self.entities,
            "relations": self.relations,
            "resources": self.resources,
            "policies": self.policies,
            "clock": self.clock,
            "version": self.version,
            "pending_effects": [effect.to_dict() for effect in self.pending_effects],
        }
        return json.dumps(data, sort_keys=True, ensure_ascii=False)

    def __repr__(self) -> str:
        entity_count = sum(len(v) for v in self.entities.values())
        return (
            f"WorldState(version={self.version}, clock={self.clock}, "
            f"entities={entity_count}, relations={len(self.relations)}, "
            f"resources={len(self.resources)}, policies={len(self.policies)}, "
            f"pending_effects={len(self.pending_effects)})"
        )
