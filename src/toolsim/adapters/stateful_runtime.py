"""Session-aware adapter for invoking stateful toolsim tools from external runtimes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from toolsim.backends.base import BaseBackend
from toolsim.backends.mock_backend import MockBackend
from toolsim.backends.sandbox_backend import SandboxBackend
from toolsim.core.environment import ToolEnvironment
from toolsim.execution.stateful_executor import ExecutorConfig, StatefulExecutor, create_default_tool_registry


@dataclass
class ToolRuntimeResponse:
    """Normalized tool execution response for external callers."""

    tool_id: str
    observation: dict[str, Any]
    success: bool
    error: str | None
    status: str
    state_changed: bool
    backend_name: str
    call_id: str
    state_hash: str
    pending_effect_count: int
    applied_effect_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_id": self.tool_id,
            "observation": self.observation,
            "success": self.success,
            "error": self.error,
            "status": self.status,
            "state_changed": self.state_changed,
            "backend_name": self.backend_name,
            "call_id": self.call_id,
            "state_hash": self.state_hash,
            "pending_effect_count": self.pending_effect_count,
            "applied_effect_count": self.applied_effect_count,
        }


class StatefulToolRuntime:
    """Manage per-session ToolEnvironment instances for stateful tool execution."""

    def __init__(
        self,
        executor: StatefulExecutor | None = None,
        executor_config: ExecutorConfig | None = None,
    ) -> None:
        self._executor_config = executor_config or ExecutorConfig()
        self._executor = executor or StatefulExecutor(create_default_tool_registry(), config=self._executor_config)
        self._sessions: dict[str, ToolEnvironment] = {}

    def execute_tool_call(
        self,
        session_id: str,
        tool_id: str,
        parameters: dict[str, Any] | None = None,
        permissions: set[str] | None = None,
        backend: str = "mock",
    ) -> ToolRuntimeResponse:
        environment = self.get_or_create_environment(session_id, backend=backend)
        record = self._executor.execute(
            tool_id,
            environment.state,
            parameters or {},
            permissions=permissions,
            environment=environment,
        )
        return ToolRuntimeResponse(
            tool_id=tool_id,
            observation=record.observation,
            success=record.success,
            error=record.error,
            status=record.status,
            state_changed=record.state_changed,
            backend_name=record.backend_name,
            call_id=record.call_id,
            state_hash=environment.state.compute_hash(),
            pending_effect_count=len(environment.state.pending_effects),
            applied_effect_count=record.applied_effect_count,
        )

    def get_or_create_environment(self, session_id: str, backend: str = "mock") -> ToolEnvironment:
        if session_id in self._sessions:
            return self._sessions[session_id]
        backend_obj = self._build_backend(session_id, backend)
        environment = ToolEnvironment(
            state=backend_obj.create_state(),
            backend=backend_obj,
            auto_advance_clock=self._executor_config.auto_advance_clock,
            auto_apply_ready_effects=self._executor_config.auto_apply_ready_effects,
        )
        self._sessions[session_id] = environment
        return environment

    def get_environment(self, session_id: str) -> ToolEnvironment | None:
        return self._sessions.get(session_id)

    def reset_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def advance_time(self, session_id: str, delta: float) -> list[dict[str, Any]]:
        environment = self.get_or_create_environment(session_id)
        results = environment.advance_time(delta)
        return [result.to_dict() for result in results]

    def _build_backend(self, session_id: str, backend: str) -> BaseBackend:
        if backend == "mock":
            return MockBackend()
        if backend == "sandbox":
            return SandboxBackend(session_id=session_id)
        raise ValueError(f"Unsupported backend: {backend}")
