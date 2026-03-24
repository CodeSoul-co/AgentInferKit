"""Core domain model for toolsim."""

from __future__ import annotations

from toolsim.core.constants import (
    CALENDAR_ALLOWED_STATUSES,
    CALENDAR_DEFAULT_ID,
    DEFAULT_AUTO_ADVANCE_CLOCK,
    DEFAULT_REINDEX_DELAY,
    EFFECT_KIND_REINDEX_FILE_SNAPSHOT,
    EffectStatus,
    EntityType,
    ExecutionStatus,
)
from toolsim.core.environment import ToolEnvironment
from toolsim.core.registry import ToolRegistry
from toolsim.core.side_effects import (
    EffectApplicationResult,
    SideEffectScheduler,
    create_default_scheduler,
)
from toolsim.core.tool_spec import (
    ConditionCheckResult,
    ExecutionContext,
    PostconditionSpec,
    PreconditionSpec,
    ToolExecutionResult,
    ToolMetadata,
    ToolSpec,
)
from toolsim.core.utils import extract_last_query_hits
from toolsim.core.world_state import (
    PendingEffect,
    PolicyDecision,
    StateSnapshot,
    WorldState,
)

__all__ = [
    # Constants
    "EntityType",
    "EffectStatus",
    "ExecutionStatus",
    "EFFECT_KIND_REINDEX_FILE_SNAPSHOT",
    "CALENDAR_DEFAULT_ID",
    "CALENDAR_ALLOWED_STATUSES",
    "DEFAULT_REINDEX_DELAY",
    "DEFAULT_AUTO_ADVANCE_CLOCK",
    # State
    "WorldState",
    "PendingEffect",
    "StateSnapshot",
    "PolicyDecision",
    # Tool spec
    "ToolSpec",
    "ToolMetadata",
    "ToolExecutionResult",
    "ExecutionContext",
    "PreconditionSpec",
    "PostconditionSpec",
    "ConditionCheckResult",
    # Environment
    "ToolEnvironment",
    # Side effects
    "SideEffectScheduler",
    "EffectApplicationResult",
    "create_default_scheduler",
    # Registry
    "ToolRegistry",
    # Utils
    "extract_last_query_hits",
]
