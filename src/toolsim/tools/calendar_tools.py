"""Calendar event tools backed by WorldState entities."""

from __future__ import annotations

from typing import Any

from toolsim.core.constants import CALENDAR_ALLOWED_STATUSES, EntityType
from toolsim.core.tool_spec import PostconditionSpec, PreconditionSpec, ToolExecutionResult, ToolMetadata, ToolSpec
from toolsim.core.world_state import WorldState

_DEFAULT_CALENDAR_ID = "default"


def _calendar_policy(state: WorldState) -> dict[str, Any]:
    """Extract calendar policy from world state."""
    policy = state.policies.get("calendar", {})
    return policy if isinstance(policy, dict) else {}


def _iter_events(state: WorldState) -> list[dict[str, Any]]:
    """Iterate over all calendar events sorted by id."""
    events = state.entities.get(EntityType.CALENDAR_EVENT, {})
    return [event for _, event in sorted(events.items())]


def _find_event(state: WorldState, event_id: str) -> dict[str, Any] | None:
    """Retrieve a single event by id, or None if absent."""
    return state.get_entity(EntityType.CALENDAR_EVENT, event_id)


def _time_overlap(start_a: float, end_a: float, start_b: float, end_b: float) -> bool:
    """Return True when two closed-open intervals overlap."""
    return start_a < end_b and start_b < end_a


def _participants_overlap(left: list[str], right: list[str]) -> bool:
    """Return True when participant lists share at least one name."""
    return bool(set(left or []) & set(right or []))


def _find_conflicts(
    state: WorldState,
    *,
    event_id: str | None,
    calendar_id: str,
    start_time: float,
    end_time: float,
    participants: list[str],
) -> list[dict[str, Any]]:
    """Return confirmed events that conflict with the given time and participants."""
    conflicts: list[dict[str, Any]] = []
    for event in _iter_events(state):
        if event_id is not None and event.get("event_id") == event_id:
            continue
        if event.get("status") != "confirmed":
            continue
        if event.get("calendar_id", _DEFAULT_CALENDAR_ID) != calendar_id:
            continue
        if not _time_overlap(
            start_time, end_time,
            float(event.get("start_time", 0.0)), float(event.get("end_time", 0.0)),
        ):
            continue
        if not _participants_overlap(participants, event.get("participants", [])):
            continue
        conflicts.append({
            "event_id": event.get("event_id"),
            "title": event.get("title"),
            "start_time": event.get("start_time"),
            "end_time": event.get("end_time"),
            "participants": event.get("participants", []),
        })
    return conflicts


def _serialize_event(event: dict[str, Any]) -> dict[str, Any]:
    """Return a serialisable snapshot of an event entity."""
    return {
        "event_id": event.get("event_id"),
        "title": event.get("title"),
        "start_time": event.get("start_time"),
        "end_time": event.get("end_time"),
        "participants": list(event.get("participants", [])),
        "location": event.get("location"),
        "description": event.get("description"),
        "status": event.get("status"),
        "calendar_id": event.get("calendar_id", _DEFAULT_CALENDAR_ID),
        "created_at": event.get("created_at"),
        "updated_at": event.get("updated_at"),
    }


class CalendarCreateEventTool(ToolSpec):
    """Create a calendar event with conflict detection and policy checks."""

    tool_name = "calendar.create_event"
    description = "Create a calendar event with conflict detection and policy checks."
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "event_id": {"type": "string"},
            "title": {"type": "string"},
            "start_time": {"type": "number"},
            "end_time": {"type": "number"},
            "participants": {"type": "array"},
            "location": {"type": "string"},
            "description": {"type": "string"},
            "calendar_id": {"type": "string"},
        },
        "required": ["event_id", "title", "start_time", "end_time", "participants"],
    }
    metadata = ToolMetadata(
        name=tool_name,
        version="0.1",
        domain="calendar",
        description=description,
        input_schema=input_schema,
        required_permissions=["calendar.create_event"],
        idempotency="non_idempotent",
    )
    preconditions = [
        PreconditionSpec(
            kind="entity_absent",
            message="Event id must be new",
            config={"entity_type": EntityType.CALENDAR_EVENT, "arg_field": "event_id"},
        )
    ]
    postconditions = [
        PostconditionSpec(
            kind="entity_exists",
            message="Created event should exist",
            config={"entity_type": EntityType.CALENDAR_EVENT, "arg_field": "event_id"},
        ),
        PostconditionSpec(kind="state_hash_changed", message="Calendar state hash should change after create"),
    ]

    def execute(self, state_or_context: Any, args: dict[str, Any]) -> ToolExecutionResult:
        state = self.get_state_from_input(state_or_context)
        clock = state_or_context.now() if hasattr(state_or_context, "now") else state.now()

        event_id = args.get("event_id")
        title = args.get("title")
        participants = list(args.get("participants") or [])
        calendar_id = args.get("calendar_id") or _DEFAULT_CALENDAR_ID

        try:
            start_time = float(args.get("start_time"))
            end_time = float(args.get("end_time"))
        except (TypeError, ValueError):
            return ToolExecutionResult(success=False, error="start_time and end_time must be numeric")

        if not event_id:
            return ToolExecutionResult(success=False, error="Missing required argument: event_id")
        if not title:
            return ToolExecutionResult(success=False, error="Missing required argument: title")
        if start_time >= end_time:
            return ToolExecutionResult(success=False, error="start_time must be less than end_time")

        policy = _calendar_policy(state)
        if calendar_id in set(policy.get("read_only_calendars", [])):
            return ToolExecutionResult(success=False, error=f"Calendar is read-only: {calendar_id}")

        allow_conflicts = bool(policy.get("allow_conflicts", False))
        conflicts = _find_conflicts(
            state,
            event_id=event_id,
            calendar_id=calendar_id,
            start_time=start_time,
            end_time=end_time,
            participants=participants,
        )
        if conflicts and not allow_conflicts:
            return ToolExecutionResult(
                success=False,
                error="Conflict detected for participant schedule",
                observation={"conflicts": conflicts, "conflict_detected": True},
            )

        event = {
            "event_id": event_id,
            "title": title,
            "start_time": start_time,
            "end_time": end_time,
            "participants": participants,
            "location": args.get("location"),
            "description": args.get("description"),
            "status": "confirmed",
            "created_at": clock,
            "updated_at": clock,
            "calendar_id": calendar_id,
        }
        state.set_entity(EntityType.CALENDAR_EVENT, event_id, event)

        return ToolExecutionResult(
            success=True,
            observation={
                "event_id": event_id,
                "status": event["status"],
                "conflict_detected": bool(conflicts),
                "created": True,
                "event": _serialize_event(event),
            },
            state_changed=True,
        )


class CalendarSearchEventsTool(ToolSpec):
    """Search calendar events by time window, participant, status, calendar, or text query."""

    tool_name = "calendar.search_events"
    description = "Search calendar events by time window, participant, status, calendar, or text query."
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "start_time": {"type": "number"},
            "end_time": {"type": "number"},
            "participant": {"type": "string"},
            "calendar_id": {"type": "string"},
            "status": {"type": "string"},
            "query": {"type": "string"},
        },
    }
    metadata = ToolMetadata(
        name=tool_name,
        version="0.1",
        domain="calendar",
        description=description,
        input_schema=input_schema,
        required_permissions=["calendar.search_events"],
        idempotency="idempotent",
    )

    def execute(self, state: WorldState, args: dict[str, Any]) -> ToolExecutionResult:
        start_time = args.get("start_time")
        end_time = args.get("end_time")
        participant = args.get("participant")
        calendar_id = args.get("calendar_id")
        status = args.get("status")
        query = (args.get("query") or "").lower()

        hits: list[dict[str, Any]] = []
        for event in _iter_events(state):
            if start_time is not None and float(event.get("end_time", 0.0)) <= float(start_time):
                continue
            if end_time is not None and float(event.get("start_time", 0.0)) >= float(end_time):
                continue
            if participant and participant not in event.get("participants", []):
                continue
            if calendar_id and event.get("calendar_id", _DEFAULT_CALENDAR_ID) != calendar_id:
                continue
            if status and event.get("status") != status:
                continue
            if query:
                haystack = " ".join(str(event.get(key) or "") for key in ["title", "location", "description"]).lower()
                if query not in haystack:
                    continue
            hits.append(_serialize_event(event))

        return ToolExecutionResult(success=True, observation={"hits": hits, "count": len(hits)}, state_changed=False)


class CalendarUpdateEventTool(ToolSpec):
    """Update an existing calendar event with conflict detection and policy checks."""

    tool_name = "calendar.update_event"
    description = "Update an existing calendar event with conflict detection and policy checks."
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "event_id": {"type": "string"},
            "title": {"type": "string"},
            "start_time": {"type": "number"},
            "end_time": {"type": "number"},
            "participants": {"type": "array"},
            "location": {"type": "string"},
            "description": {"type": "string"},
            "status": {"type": "string"},
        },
        "required": ["event_id"],
    }
    metadata = ToolMetadata(
        name=tool_name,
        version="0.1",
        domain="calendar",
        description=description,
        input_schema=input_schema,
        required_permissions=["calendar.update_event"],
        idempotency="non_idempotent",
    )
    preconditions = [
        PreconditionSpec(
            kind="entity_exists",
            message="Event must exist before update",
            config={"entity_type": EntityType.CALENDAR_EVENT, "arg_field": "event_id"},
        )
    ]
    postconditions = [
        PostconditionSpec(kind="state_hash_changed", message="Calendar state hash should change after update")
    ]

    def execute(self, state_or_context: Any, args: dict[str, Any]) -> ToolExecutionResult:
        state = self.get_state_from_input(state_or_context)
        clock = state_or_context.now() if hasattr(state_or_context, "now") else state.now()
        event_id = args.get("event_id")
        if not event_id:
            return ToolExecutionResult(success=False, error="Missing required argument: event_id")

        existing = _find_event(state, event_id)
        if existing is None:
            return ToolExecutionResult(success=False, error=f"Event not found: {event_id!r}")

        updated = dict(existing)
        for field in ["title", "location", "description"]:
            if field in args:
                updated[field] = args.get(field)
        if "participants" in args:
            updated["participants"] = list(args.get("participants") or [])
        if "start_time" in args:
            updated["start_time"] = float(args.get("start_time"))
        if "end_time" in args:
            updated["end_time"] = float(args.get("end_time"))
        if "status" in args:
            new_status = args.get("status")
            if new_status not in CALENDAR_ALLOWED_STATUSES:
                return ToolExecutionResult(success=False, error=f"Unsupported status: {new_status!r}")
            updated["status"] = new_status

        if float(updated["start_time"]) >= float(updated["end_time"]):
            return ToolExecutionResult(success=False, error="start_time must be less than end_time")

        policy = _calendar_policy(state)
        calendar_id = updated.get("calendar_id", _DEFAULT_CALENDAR_ID)
        if calendar_id in set(policy.get("read_only_calendars", [])):
            return ToolExecutionResult(success=False, error=f"Calendar is read-only: {calendar_id}")

        allow_conflicts = bool(policy.get("allow_conflicts", False))
        conflicts = _find_conflicts(
            state,
            event_id=event_id,
            calendar_id=calendar_id,
            start_time=float(updated["start_time"]),
            end_time=float(updated["end_time"]),
            participants=list(updated.get("participants", [])),
        )
        if conflicts and not allow_conflicts and updated.get("status", "confirmed") == "confirmed":
            return ToolExecutionResult(
                success=False,
                error="Conflict detected for participant schedule",
                observation={"conflicts": conflicts, "conflict_detected": True},
            )

        updated["updated_at"] = clock
        state.set_entity(EntityType.CALENDAR_EVENT, event_id, updated)
        return ToolExecutionResult(
            success=True,
            observation={
                "event_id": event_id,
                "updated": True,
                "event": _serialize_event(updated),
                "conflict_detected": bool(conflicts),
            },
            state_changed=True,
        )


class CalendarDeleteEventTool(ToolSpec):
    """Soft-delete a calendar event by marking it cancelled."""

    tool_name = "calendar.delete_event"
    description = "Soft-delete a calendar event by marking it cancelled."
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {"event_id": {"type": "string"}},
        "required": ["event_id"],
    }
    metadata = ToolMetadata(
        name=tool_name,
        version="0.1",
        domain="calendar",
        description=description,
        input_schema=input_schema,
        required_permissions=["calendar.delete_event"],
        idempotency="non_idempotent",
    )
    preconditions = [
        PreconditionSpec(
            kind="entity_exists",
            message="Event must exist before delete",
            config={"entity_type": EntityType.CALENDAR_EVENT, "arg_field": "event_id"},
        )
    ]
    postconditions = [
        PostconditionSpec(
            kind="entity_field_equals",
            message="Deleted event should be marked cancelled",
            config={"entity_type": EntityType.CALENDAR_EVENT, "arg_field": "event_id", "field": "status", "expected": "cancelled"},
        )
    ]

    def execute(self, state_or_context: Any, args: dict[str, Any]) -> ToolExecutionResult:
        state = self.get_state_from_input(state_or_context)
        clock = state_or_context.now() if hasattr(state_or_context, "now") else state.now()
        event_id = args.get("event_id")
        if not event_id:
            return ToolExecutionResult(success=False, error="Missing required argument: event_id")

        event = _find_event(state, event_id)
        if event is None:
            return ToolExecutionResult(success=False, error=f"Event not found: {event_id!r}")

        policy = _calendar_policy(state)
        if not bool(policy.get("allow_delete_started_event", False)) and state.now() >= float(event.get("start_time", 0.0)):
            return ToolExecutionResult(success=False, error="Policy forbids deleting an event that has already started")

        updated = dict(event)
        updated["status"] = "cancelled"
        updated["updated_at"] = clock
        state.set_entity(EntityType.CALENDAR_EVENT, event_id, updated)
        return ToolExecutionResult(
            success=True,
            observation={"event_id": event_id, "deleted": True, "event": _serialize_event(updated)},
            state_changed=True,
        )


CALENDAR_TOOLS: dict[str, ToolSpec] = {
    tool.tool_name: tool
    for tool in [
        CalendarCreateEventTool(),
        CalendarSearchEventsTool(),
        CalendarUpdateEventTool(),
        CalendarDeleteEventTool(),
    ]
}
