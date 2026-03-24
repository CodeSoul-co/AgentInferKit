"""Execution environment wrapping WorldState, backend, and delayed side-effect scheduler."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from toolsim.backends.base import BaseBackend
from toolsim.backends.mock_backend import MockBackend
from toolsim.core.side_effects import EffectApplicationResult, SideEffectScheduler, create_default_scheduler
from toolsim.core.world_state import WorldState


@dataclass
class ToolEnvironment:
    """Execution environment around WorldState, backend, and delayed side effects."""

    state: WorldState
    backend: BaseBackend = field(default_factory=MockBackend)
    scheduler: SideEffectScheduler = field(default_factory=create_default_scheduler)
    auto_advance_clock: float = 0.0
    auto_apply_ready_effects: bool = True

    def before_call(self, tool_name: str, args: dict[str, Any]) -> None:
        """Run before each tool call: advance clock and flush ready effects."""
        if self.auto_advance_clock:
            self.state.advance_clock(self.auto_advance_clock)
        if self.auto_apply_ready_effects:
            self.apply_ready_effects()

    def after_call(self, tool_name: str, args: dict[str, Any], result: Any) -> list[EffectApplicationResult]:
        """Run after each tool call: flush ready effects if configured."""
        if self.auto_apply_ready_effects:
            return self.apply_ready_effects()
        return []

    def advance_time(self, delta: float) -> list[EffectApplicationResult]:
        """Advance the world clock and flush ready effects."""
        self.state.advance_clock(delta)
        if self.auto_apply_ready_effects:
            return self.apply_ready_effects()
        return []

    def apply_ready_effects(self) -> list[EffectApplicationResult]:
        """Apply all pending effects that are due."""
        return self.scheduler.apply_ready_effects(self.state)

    def run_until_idle(self, max_steps: int = 100) -> list[EffectApplicationResult]:
        """Repeatedly apply ready effects until none remain (or max_steps is reached)."""
        results: list[EffectApplicationResult] = []
        for _ in range(max_steps):
            batch = self.apply_ready_effects()
            if not batch:
                break
            results.extend(batch)
        return results

    def snapshot(self, label: str | None = None) -> str:
        """Create a named state snapshot and return its id."""
        return self.backend.snapshot_state(self.state, label=label)

    def rollback(self, snapshot_id: str) -> bool:
        """Roll back to a previously snapshot. Returns True on success."""
        return self.backend.rollback_state(self.state, snapshot_id)
