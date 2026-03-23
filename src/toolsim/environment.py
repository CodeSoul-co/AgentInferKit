from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from toolsim.backends.base import BaseBackend
from toolsim.backends.mock_backend import MockBackend
from toolsim.side_effects import EffectApplicationResult, SideEffectScheduler, create_default_scheduler
from toolsim.world_state import WorldState


@dataclass
class ToolEnvironment:
    """Execution environment around WorldState, backend, and delayed side effects."""

    state: WorldState
    backend: BaseBackend = field(default_factory=MockBackend)
    scheduler: SideEffectScheduler = field(default_factory=create_default_scheduler)
    auto_advance_clock: float = 0.0
    auto_apply_ready_effects: bool = True

    def before_call(self, tool_name: str, args: Dict[str, Any]) -> None:
        if self.auto_advance_clock:
            self.state.advance_clock(self.auto_advance_clock)
        if self.auto_apply_ready_effects:
            self.apply_ready_effects()

    def after_call(self, tool_name: str, args: Dict[str, Any], result: Any) -> List[EffectApplicationResult]:
        if self.auto_apply_ready_effects:
            return self.apply_ready_effects()
        return []

    def advance_time(self, delta: float) -> List[EffectApplicationResult]:
        self.state.advance_clock(delta)
        if self.auto_apply_ready_effects:
            return self.apply_ready_effects()
        return []

    def apply_ready_effects(self) -> List[EffectApplicationResult]:
        return self.scheduler.apply_ready_effects(self.state)

    def run_until_idle(self, max_steps: int = 100) -> List[EffectApplicationResult]:
        results: List[EffectApplicationResult] = []
        for _ in range(max_steps):
            batch = self.apply_ready_effects()
            if not batch:
                break
            results.extend(batch)
        return results

    def snapshot(self, label: Optional[str] = None) -> str:
        return self.backend.snapshot_state(self.state, label=label)

    def rollback(self, snapshot_id: str) -> bool:
        return self.backend.rollback_state(self.state, snapshot_id)
