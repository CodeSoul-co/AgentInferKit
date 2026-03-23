from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set

from toolsim.world_state import WorldState

if TYPE_CHECKING:
    from toolsim.backends.base import BaseBackend
    from toolsim.environment import ToolEnvironment


@dataclass
class ToolMetadata:
    name: str
    version: str = "0.1"
    domain: str = "generic"
    description: str = ""
    tags: List[str] = field(default_factory=list)
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    required_permissions: List[str] = field(default_factory=list)
    idempotency: str = "unknown"
    supports_partial: bool = False
    supports_async: bool = False


@dataclass
class ConditionCheckResult:
    kind: str
    passed: bool
    message: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"kind": self.kind, "passed": self.passed, "message": self.message, "details": self.details}


@dataclass
class PreconditionSpec:
    kind: str
    message: str = ""
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PostconditionSpec:
    kind: str
    message: str = ""
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionContext:
    state: WorldState
    call_id: str
    clock: float
    permissions: Set[str] = field(default_factory=set)
    timeout_ms: Optional[int] = None
    attempt: int = 1
    max_attempts: int = 1
    labels: Dict[str, Any] = field(default_factory=dict)
    environment: Optional["ToolEnvironment"] = None
    backend: Optional["BaseBackend"] = None

    def now(self) -> float:
        return self.clock

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions


@dataclass
class ToolExecutionResult:
    success: bool
    status: str = "succeeded"
    observation: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    state_changed: bool = False
    partial: bool = False
    pending: bool = False
    scheduled_effects: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.status == "succeeded" and not self.success:
            self.status = "failed"
        if self.partial:
            self.status = "partial"
        if self.pending:
            self.status = "pending"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "success": self.success,
            "observation": self.observation,
            "error": self.error,
            "state_changed": self.state_changed,
            "partial": self.partial,
            "pending": self.pending,
            "scheduled_effects": self.scheduled_effects,
            "metadata": self.metadata,
        }


class ToolSpec(ABC):
    tool_name: str = ""
    description: str = ""
    input_schema: Dict[str, Any] = {}
    metadata: Optional[ToolMetadata] = None
    preconditions: List[PreconditionSpec] = []
    postconditions: List[PostconditionSpec] = []

    @abstractmethod
    def execute(self, state_or_context: Any, args: Dict[str, Any]) -> ToolExecutionResult:
        """Execute the tool against a WorldState or ExecutionContext."""

    def get_metadata(self) -> ToolMetadata:
        if self.metadata is not None:
            return self.metadata
        return ToolMetadata(name=getattr(self, "tool_name", self.__class__.__name__), description=getattr(self, "description", ""), input_schema=getattr(self, "input_schema", {}) or {})

    def get_preconditions(self) -> List[PreconditionSpec]:
        return list(getattr(self, "preconditions", []) or [])

    def get_postconditions(self) -> List[PostconditionSpec]:
        return list(getattr(self, "postconditions", []) or [])

    def get_state_from_input(self, state_or_context: Any) -> WorldState:
        if isinstance(state_or_context, ExecutionContext):
            return state_or_context.state
        return state_or_context

    def __repr__(self) -> str:
        metadata = self.get_metadata()
        return f"{self.__class__.__name__}(tool_name={metadata.name!r}, version={metadata.version!r})"
