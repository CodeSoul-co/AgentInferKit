from __future__ import annotations

from typing import Any, Optional

from toolsim.backends.sandbox_backend import SandboxBackend
from toolsim.core.world_state import WorldState
from toolsim.tools.apibank_runtime import (
    APIBANK_ACCOUNT_DATABASE,
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


class LiveLikeBackend(SandboxBackend):
    """Deterministic live-like backend used for migration experiments.

    This backend keeps the isolated, reproducible state semantics of
    ``SandboxBackend`` while adding an API-Bank-compatible runtime for account,
    agenda, and meeting databases plus a ToolSandbox-compatible runtime for
    settings, contacts, messages, and reminders. Fault profiles still supply
    network-like failures, but successful benchmark calls now execute stateful
    workflows against session state.
    """

    def __init__(self, session_id: Optional[str] = None) -> None:
        super().__init__(session_id=session_id)

    def get_backend_name(self) -> str:
        return "live_like"

    def create_state(self) -> WorldState:
        state = super().create_state()
        state.resources["live_like_session"] = self.session_id
        state.policies.setdefault("backend", {})
        state.policies["backend"]["realism"] = "live_like"
        state.policies["backend"]["api_bank_runtime"] = APIBANK_RUNTIME_NAME
        state.policies["backend"]["toolsandbox_runtime"] = TOOLSANDBOX_RUNTIME_NAME
        self.ensure_apibank_account_state(state)
        self.ensure_toolsandbox_state(state)
        return state

    def clone_state(self, state: WorldState) -> WorldState:
        cloned = super().clone_state(state)
        cloned.resources["live_like_session"] = self.session_id
        cloned.policies.setdefault("backend", {})
        cloned.policies["backend"]["realism"] = "live_like"
        cloned.policies["backend"]["api_bank_runtime"] = APIBANK_RUNTIME_NAME
        cloned.policies["backend"]["toolsandbox_runtime"] = TOOLSANDBOX_RUNTIME_NAME
        return cloned

    def ensure_apibank_account_state(self, state: WorldState) -> None:
        """Seed the supported API-Bank databases if the case did not provide them."""
        ensure_apibank_state(state)
        state.resources.setdefault("api_bank_session", self.session_id)
        self._persist_account_database(state)

    def call_apibank_api(self, state: WorldState, api_name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Run one API-Bank API through the live-like runtime."""
        self.ensure_apibank_account_state(state)
        result = call_apibank_api(state, api_name, args)
        self._persist_account_database(state)
        return result

    def ensure_toolsandbox_state(self, state: WorldState) -> None:
        """Seed and persist ToolSandbox-style databases for this live-like session."""
        ensure_toolsandbox_state(state)
        state.resources.setdefault("toolsandbox_session", self.session_id)
        self._persist_toolsandbox_database(state)

    def call_toolsandbox_tool(self, state: WorldState, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Run one ToolSandbox tool through the live-like runtime."""
        self.ensure_toolsandbox_state(state)
        result = call_toolsandbox_tool(state, tool_name, args)
        self._persist_toolsandbox_database(state)
        return result

    def record_toolsandbox_end_conversation(self, state: WorldState, args: dict[str, Any]) -> dict[str, Any]:
        self.ensure_toolsandbox_state(state)
        result = record_end_conversation(state, args)
        self._persist_toolsandbox_database(state)
        return result

    def call_apibank_forgot_password(self, state: WorldState, args: dict[str, Any]) -> dict[str, Any]:
        """Backward-compatible wrapper for the first API-Bank tool added here."""
        return self.call_apibank_api(state, "ForgotPassword", args)

    def _persist_account_database(self, state: WorldState) -> None:
        persist_apibank_databases(state, self.session_root)

    def _persist_toolsandbox_database(self, state: WorldState) -> None:
        persist_toolsandbox_databases(state, self.session_root)
