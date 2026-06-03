from __future__ import annotations

from typing import Optional

from toolsim.backends.sandbox_backend import SandboxBackend
from toolsim.core.world_state import WorldState


class LiveLikeBackend(SandboxBackend):
    """Deterministic live-like backend used for migration experiments.

    This backend keeps the isolated, reproducible state semantics of
    ``SandboxBackend`` while marking the execution substrate as live-like. The
    live-like behavior itself is supplied by the runner through structured fault
    profiles so the experiment remains reproducible.
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
        return state

    def clone_state(self, state: WorldState) -> WorldState:
        cloned = super().clone_state(state)
        cloned.resources["live_like_session"] = self.session_id
        cloned.policies.setdefault("backend", {})
        cloned.policies["backend"]["realism"] = "live_like"
        return cloned
