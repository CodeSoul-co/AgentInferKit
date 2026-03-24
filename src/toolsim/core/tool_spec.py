"""Abstract tool specification and supporting data classes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from toolsim.backends.base import BaseBackend
    from toolsim.core.environment import ToolEnvironment


@dataclass
class ToolMetadata:
    """Metadata describing a tool's interface and requirements."""

    name: str
    version: str = "0.1"
    domain: str = "generic"
    description: str = ""
    tags: list[str] = field(default_factory=list)
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    required_permissions: list[str] = field(default_factory=list)
    idempotency: str = "unknown"
    supports_partial: bool = False
    supports_async: bool = False


@dataclass
class ConditionCheckResult:
    """Result of evaluating a precondition or postcondition check."""

    kind: str
    passed: bool
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "passed": self.passed, "message": self.message, "details": self.details}


@dataclass
class PreconditionSpec:
    """Specification for a precondition that must hold before tool execution."""

    kind: str
    message: str = ""
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class PostconditionSpec:
    """Specification for a postcondition that must hold after tool execution."""

    kind: str
    message: str = ""
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionContext:
    """Context object passed to a tool at execution time."""

    state: "WorldState"
    call_id: str
    clock: float
    permissions: set[str] = field(default_factory=set)
    timeout_ms: int | None = None
    attempt: int = 1
    max_attempts: int = 1
    labels: dict[str, Any] = field(default_factory=dict)
    environment: "ToolEnvironment | None" = None
    backend: "BaseBackend | None" = None

    def now(self) -> float:
        """Return the current logical clock value."""
        return self.clock

    def has_permission(self, permission: str) -> bool:
        """Check whether a permission is present in this context."""
        return permission in self.permissions


@dataclass
class ToolExecutionResult:
    """Result returned by a tool's execute() method."""

    success: bool
    status: str = "succeeded"
    observation: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    state_changed: bool = False
    partial: bool = False
    pending: bool = False
    scheduled_effects: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.status == "succeeded" and not self.success:
            self.status = "failed"
        if self.partial:
            self.status = "partial"
        if self.pending:
            self.status = "pending"

    def to_dict(self) -> dict[str, Any]:
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
    """Abstract base class that all toolsim tools must inherit from."""

    tool_name: str = ""
    description: str = ""
    input_schema: dict[str, Any] = {}
    metadata: ToolMetadata | None = None
    preconditions: list[PreconditionSpec] = []
    postconditions: list[PostconditionSpec] = []

    @abstractmethod
    def execute(self, state_or_context: Any, args: dict[str, Any]) -> ToolExecutionResult:
        """Execute the tool against a WorldState or ExecutionContext."""

    def get_metadata(self) -> ToolMetadata:
        """Return the tool's metadata, building a default if none was set."""
        if self.metadata is not None:
            return self.metadata
        return ToolMetadata(
            name=getattr(self, "tool_name", self.__class__.__name__),
            description=getattr(self, "description", ""),
            input_schema=getattr(self, "input_schema", {}) or {},
        )

    def get_preconditions(self) -> list[PreconditionSpec]:
        """Return the list of preconditions for this tool."""
        return list(getattr(self, "preconditions", []) or [])

    def get_postconditions(self) -> list[PostconditionSpec]:
        """Return the list of postconditions for this tool."""
        return list(getattr(self, "postconditions", []) or [])

    def get_state_from_input(self, state_or_context: Any) -> "WorldState":
        """Extract WorldState from the execute() argument, which may be a state or context."""
        if isinstance(state_or_context, ExecutionContext):
            return state_or_context.state
        return state_or_context

    def __repr__(self) -> str:
        metadata = self.get_metadata()
        return f"{self.__class__.__name__}(tool_name={metadata.name!r}, version={metadata.version!r})"
