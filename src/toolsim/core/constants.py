"""Shared constants and enums for toolsim.

Centralises all magic strings and numeric constants used across modules,
replacing hardcoded literals with typed identifiers for better
maintainability and IDE support.
"""

from __future__ import annotations

from enum import Enum


# ---------------------------------------------------------------------------
# Entity types
# ---------------------------------------------------------------------------

class EntityType(str, Enum):
    """Canonical names for entity types stored in WorldState."""

    FILE = "file"
    SEARCH_INDEX = "search_index"
    CALENDAR_EVENT = "calendar_event"


# ---------------------------------------------------------------------------
# Effect lifecycle
# ---------------------------------------------------------------------------

class EffectStatus(str, Enum):
    """Lifecycle states of a PendingEffect."""

    PENDING = "pending"
    APPLIED = "applied"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Tool execution result status
# ---------------------------------------------------------------------------

class ExecutionStatus(str, Enum):
    """High-level outcome of a tool execution call."""

    SUCCEEDED = "succeeded"
    FAILED = "failed"
    PARTIAL = "partial"
    PENDING = "pending"


# ---------------------------------------------------------------------------
# Effect kind identifiers
# ---------------------------------------------------------------------------

EFFECT_KIND_REINDEX_FILE_SNAPSHOT = "search.reindex_file_snapshot"


# ---------------------------------------------------------------------------
# Calendar constants
# ---------------------------------------------------------------------------

CALENDAR_DEFAULT_ID = "default"
CALENDAR_ALLOWED_STATUSES = frozenset({"confirmed", "cancelled"})


# ---------------------------------------------------------------------------
# File tool constants
# ---------------------------------------------------------------------------

FILE_TOOL_NAME_WRITE = "file.write"
FILE_TOOL_NAME_READ = "file.read"

SEARCH_TOOL_NAME_INDEX = "search.index"
SEARCH_TOOL_NAME_QUERY = "search.query"

CALENDAR_TOOL_NAME_CREATE = "calendar.create_event"
CALENDAR_TOOL_NAME_SEARCH = "calendar.search_events"
CALENDAR_TOOL_NAME_UPDATE = "calendar.update_event"
CALENDAR_TOOL_NAME_DELETE = "calendar.delete_event"


# ---------------------------------------------------------------------------
# Numeric defaults
# ---------------------------------------------------------------------------

DEFAULT_REINDEX_DELAY = 1.0
DEFAULT_AUTO_ADVANCE_CLOCK = 0.0
