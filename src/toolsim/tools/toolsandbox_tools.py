"""Minimal ToolSandbox-compatible tools.

These tools are not intended to emulate the full ToolSandbox mobile runtime.
They provide a deterministic in-process bridge so ToolSandbox scenarios can be
loaded, converted, executed, traced, and evaluated inside AgentInferKit.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from toolsim.core.tool_spec import ToolExecutionResult, ToolMetadata, ToolSpec
from toolsim.core.world_state import WorldState


CONTACT = "contact"
REMINDER = "reminder"
MESSAGE = "messaging"
SETTING = "setting"
SANDBOX = "sandbox"


def _now(state: WorldState) -> float:
    return state.now()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def _settings_entity(state: WorldState) -> dict[str, Any]:
    entity = state.get_entity(SETTING, "device")
    if entity is None:
        entity = {}
        state.set_entity(SETTING, "device", entity)
    return dict(entity)


def _set_settings_entity(state: WorldState, entity: dict[str, Any]) -> None:
    state.set_entity(SETTING, "device", entity)


def _record_sandbox_event(
    state: WorldState,
    *,
    sender: str,
    recipient: str,
    content: str | None = None,
    tool_name: str | None = None,
    arguments: dict[str, Any] | None = None,
) -> dict[str, Any]:
    event_id = _new_id("sandbox")
    event = {
        "sandbox_message_index": len(state.entities.get(SANDBOX, {})),
        "sender": sender,
        "recipient": recipient,
        "content": content,
        "conversation_active": recipient != "END",
        "openai_function_name": tool_name,
        "openai_tool_call_id": event_id if tool_name else None,
        "tool_call_exception": None,
        "tool_trace": json.dumps({"tool_name": tool_name, "arguments": arguments or {}}, sort_keys=True) if tool_name else None,
        "visible_to": [recipient],
        "created_at": _now(state),
    }
    state.set_entity(SANDBOX, event_id, event)
    return event


def _find_record(state: WorldState, entity_type: str, **criteria: Any) -> tuple[str, dict[str, Any]] | tuple[None, None]:
    for record_id, record in state.entities.get(entity_type, {}).items():
        if all(value is None or record.get(key) == value for key, value in criteria.items()):
            return record_id, record
    return None, None


class AddContactTool(ToolSpec):
    tool_name = "add_contact"
    metadata = ToolMetadata(name=tool_name, version="0.1", domain="toolsandbox.contacts")

    def execute(self, state: WorldState, args: dict[str, Any]) -> ToolExecutionResult:
        person_id = args.get("person_id") or _new_id("person")
        contact = {
            "person_id": person_id,
            "name": args.get("name"),
            "phone_number": args.get("phone_number"),
            "relationship": args.get("relationship"),
            "is_self": bool(args.get("is_self", False)),
            "sandbox_message_index": args.get("sandbox_message_index"),
            "created_at": _now(state),
            "updated_at": _now(state),
        }
        state.set_entity(CONTACT, person_id, contact)
        _record_sandbox_event(state, sender="EXECUTION_ENVIRONMENT", recipient="AGENT", tool_name=self.tool_name, arguments=args)
        return ToolExecutionResult(success=True, observation={"contact": contact}, state_changed=True)


class ModifyContactTool(ToolSpec):
    tool_name = "modify_contact"
    metadata = ToolMetadata(name=tool_name, version="0.1", domain="toolsandbox.contacts")

    def execute(self, state: WorldState, args: dict[str, Any]) -> ToolExecutionResult:
        record_id, contact = _find_record(
            state,
            CONTACT,
            person_id=args.get("person_id"),
            name=args.get("name"),
            phone_number=args.get("phone_number"),
        )
        if contact is None:
            record_id = args.get("person_id") or _new_id("person")
            contact = {
                "person_id": record_id,
                "name": None,
                "phone_number": None,
                "relationship": None,
                "is_self": False,
                "sandbox_message_index": None,
                "created_at": _now(state),
            }
        updated = dict(contact)
        for field in ["name", "phone_number", "relationship", "is_self"]:
            if field in args:
                updated[field] = args[field]
        updated["updated_at"] = _now(state)
        state.set_entity(CONTACT, record_id, updated)
        _record_sandbox_event(state, sender="EXECUTION_ENVIRONMENT", recipient="AGENT", tool_name=self.tool_name, arguments=args)
        return ToolExecutionResult(success=True, observation={"contact": updated}, state_changed=True)


class RemoveContactTool(ToolSpec):
    tool_name = "remove_contact"
    metadata = ToolMetadata(name=tool_name, version="0.1", domain="toolsandbox.contacts")

    def execute(self, state: WorldState, args: dict[str, Any]) -> ToolExecutionResult:
        record_id, _ = _find_record(state, CONTACT, person_id=args.get("person_id"), name=args.get("name"), phone_number=args.get("phone_number"))
        if record_id is None:
            return ToolExecutionResult(success=False, error="Contact not found")
        state.delete_entity(CONTACT, record_id)
        _record_sandbox_event(state, sender="EXECUTION_ENVIRONMENT", recipient="AGENT", tool_name=self.tool_name, arguments=args)
        return ToolExecutionResult(success=True, observation={"removed": True}, state_changed=True)


class SearchContactsTool(ToolSpec):
    tool_name = "search_contacts"
    metadata = ToolMetadata(name=tool_name, version="0.1", domain="toolsandbox.contacts")

    def execute(self, state: WorldState, args: dict[str, Any]) -> ToolExecutionResult:
        query = str(args.get("query") or args.get("name") or args.get("phone_number") or "").lower()
        hits = []
        for contact in state.entities.get(CONTACT, {}).values():
            haystack = " ".join(str(contact.get(k) or "") for k in ["name", "phone_number", "relationship"]).lower()
            if not query or query in haystack:
                hits.append(contact)
        _record_sandbox_event(state, sender="EXECUTION_ENVIRONMENT", recipient="AGENT", tool_name=self.tool_name, arguments=args)
        return ToolExecutionResult(success=True, observation={"hits": hits, "count": len(hits)}, state_changed=True)


class SetSettingTool(ToolSpec):
    def __init__(self, tool_name: str, field_name: str) -> None:
        self.tool_name = tool_name
        self.field_name = field_name
        self.metadata = ToolMetadata(name=tool_name, version="0.1", domain="toolsandbox.settings")

    def execute(self, state: WorldState, args: dict[str, Any]) -> ToolExecutionResult:
        settings = _settings_entity(state)
        value = args.get(self.field_name)
        if value is None:
            value = args.get("status")
        if value is None:
            value = args.get("enabled")
        settings[self.field_name] = bool(value)
        settings["updated_at"] = _now(state)
        _set_settings_entity(state, settings)
        _record_sandbox_event(state, sender="EXECUTION_ENVIRONMENT", recipient="AGENT", tool_name=self.tool_name, arguments=args)
        return ToolExecutionResult(success=True, observation={self.field_name: settings[self.field_name]}, state_changed=True)


class GetSettingTool(ToolSpec):
    def __init__(self, tool_name: str, field_name: str) -> None:
        self.tool_name = tool_name
        self.field_name = field_name
        self.metadata = ToolMetadata(name=tool_name, version="0.1", domain="toolsandbox.settings")

    def execute(self, state: WorldState, args: dict[str, Any]) -> ToolExecutionResult:
        settings = _settings_entity(state)
        _record_sandbox_event(state, sender="EXECUTION_ENVIRONMENT", recipient="AGENT", tool_name=self.tool_name, arguments=args)
        return ToolExecutionResult(success=True, observation={self.field_name: settings.get(self.field_name)}, state_changed=True)


class GetCurrentLocationTool(ToolSpec):
    tool_name = "get_current_location"
    metadata = ToolMetadata(name=tool_name, version="0.1", domain="toolsandbox.settings")

    def execute(self, state: WorldState, args: dict[str, Any]) -> ToolExecutionResult:
        settings = _settings_entity(state)
        _record_sandbox_event(state, sender="EXECUTION_ENVIRONMENT", recipient="AGENT", tool_name=self.tool_name, arguments=args)
        return ToolExecutionResult(
            success=True,
            observation={"latitude": settings.get("latitude"), "longitude": settings.get("longitude")},
            state_changed=True,
        )


class AddReminderTool(ToolSpec):
    tool_name = "add_reminder"
    metadata = ToolMetadata(name=tool_name, version="0.1", domain="toolsandbox.reminders")

    def execute(self, state: WorldState, args: dict[str, Any]) -> ToolExecutionResult:
        reminder_id = args.get("reminder_id") or _new_id("reminder")
        reminder = {
            "reminder_id": reminder_id,
            "content": args.get("content"),
            "reminder_timestamp": args.get("reminder_timestamp"),
            "latitude": args.get("latitude"),
            "longitude": args.get("longitude"),
            "sandbox_message_index": args.get("sandbox_message_index"),
            "creation_timestamp": _now(state),
            "updated_at": _now(state),
        }
        state.set_entity(REMINDER, reminder_id, reminder)
        _record_sandbox_event(state, sender="EXECUTION_ENVIRONMENT", recipient="AGENT", tool_name=self.tool_name, arguments=args)
        return ToolExecutionResult(success=True, observation={"reminder": reminder}, state_changed=True)


class ModifyReminderTool(ToolSpec):
    tool_name = "modify_reminder"
    metadata = ToolMetadata(name=tool_name, version="0.1", domain="toolsandbox.reminders")

    def execute(self, state: WorldState, args: dict[str, Any]) -> ToolExecutionResult:
        record_id, reminder = _find_record(state, REMINDER, reminder_id=args.get("reminder_id"), content=args.get("content"))
        if reminder is None:
            record_id = args.get("reminder_id") or _new_id("reminder")
            reminder = {
                "reminder_id": record_id,
                "content": None,
                "reminder_timestamp": None,
                "latitude": None,
                "longitude": None,
                "sandbox_message_index": None,
                "creation_timestamp": _now(state),
            }
        updated = dict(reminder)
        for field in ["content", "reminder_timestamp", "latitude", "longitude"]:
            if field in args:
                updated[field] = args[field]
        updated["updated_at"] = _now(state)
        state.set_entity(REMINDER, record_id, updated)
        _record_sandbox_event(state, sender="EXECUTION_ENVIRONMENT", recipient="AGENT", tool_name=self.tool_name, arguments=args)
        return ToolExecutionResult(success=True, observation={"reminder": updated}, state_changed=True)


class RemoveReminderTool(ToolSpec):
    tool_name = "remove_reminder"
    metadata = ToolMetadata(name=tool_name, version="0.1", domain="toolsandbox.reminders")

    def execute(self, state: WorldState, args: dict[str, Any]) -> ToolExecutionResult:
        record_id, _ = _find_record(state, REMINDER, reminder_id=args.get("reminder_id"), content=args.get("content"))
        if record_id is None:
            return ToolExecutionResult(success=False, error="Reminder not found")
        state.delete_entity(REMINDER, record_id)
        _record_sandbox_event(state, sender="EXECUTION_ENVIRONMENT", recipient="AGENT", tool_name=self.tool_name, arguments=args)
        return ToolExecutionResult(success=True, observation={"removed": True}, state_changed=True)


class SearchReminderTool(ToolSpec):
    tool_name = "search_reminder"
    metadata = ToolMetadata(name=tool_name, version="0.1", domain="toolsandbox.reminders")

    def execute(self, state: WorldState, args: dict[str, Any]) -> ToolExecutionResult:
        query = str(args.get("query") or args.get("content") or "").lower()
        hits = []
        for reminder in state.entities.get(REMINDER, {}).values():
            if not query or query in str(reminder.get("content") or "").lower():
                hits.append(reminder)
        _record_sandbox_event(state, sender="EXECUTION_ENVIRONMENT", recipient="AGENT", tool_name=self.tool_name, arguments=args)
        return ToolExecutionResult(success=True, observation={"hits": hits, "count": len(hits)}, state_changed=True)


class SendMessageTool(ToolSpec):
    tool_name = "send_message_with_phone_number"
    metadata = ToolMetadata(name=tool_name, version="0.1", domain="toolsandbox.messaging")

    def execute(self, state: WorldState, args: dict[str, Any]) -> ToolExecutionResult:
        message_id = args.get("message_id") or _new_id("message")
        message = {
            "message_id": message_id,
            "recipient_phone_number": args.get("recipient_phone_number"),
            "sender_phone_number": args.get("sender_phone_number"),
            "recipient_person_id": args.get("recipient_person_id"),
            "sender_person_id": args.get("sender_person_id"),
            "content": args.get("content"),
            "creation_timestamp": _now(state),
            "sandbox_message_index": args.get("sandbox_message_index"),
        }
        state.set_entity(MESSAGE, message_id, message)
        _record_sandbox_event(state, sender="EXECUTION_ENVIRONMENT", recipient="AGENT", tool_name=self.tool_name, arguments=args)
        return ToolExecutionResult(success=True, observation={"message": message}, state_changed=True)


class SearchMessagesTool(ToolSpec):
    tool_name = "search_messages"
    metadata = ToolMetadata(name=tool_name, version="0.1", domain="toolsandbox.messaging")

    def execute(self, state: WorldState, args: dict[str, Any]) -> ToolExecutionResult:
        query = str(args.get("query") or args.get("content") or "").lower()
        hits = []
        for message in state.entities.get(MESSAGE, {}).values():
            if not query or query in str(message.get("content") or "").lower():
                hits.append(message)
        _record_sandbox_event(state, sender="EXECUTION_ENVIRONMENT", recipient="AGENT", tool_name=self.tool_name, arguments=args)
        return ToolExecutionResult(success=True, observation={"hits": hits, "count": len(hits)}, state_changed=True)


class EndConversationTool(ToolSpec):
    tool_name = "end_conversation"
    metadata = ToolMetadata(name=tool_name, version="0.1", domain="toolsandbox.sandbox")

    def execute(self, state: WorldState, args: dict[str, Any]) -> ToolExecutionResult:
        content = args.get("content")
        if content:
            _record_sandbox_event(state, sender="AGENT", recipient=args.get("recipient", "USER"), content=content)
        event = _record_sandbox_event(state, sender="AGENT", recipient="END", tool_name=self.tool_name, arguments=args)
        return ToolExecutionResult(success=True, observation={"ended": True, "event": event}, state_changed=True)


class GenericToolTraceTool(ToolSpec):
    """Track a ToolSandbox helper tool call without external side effects."""

    def __init__(self, tool_name: str) -> None:
        self.tool_name = tool_name
        self.metadata = ToolMetadata(name=tool_name, version="0.1", domain="toolsandbox.helper")

    def execute(self, state: WorldState, args: dict[str, Any]) -> ToolExecutionResult:
        event = _record_sandbox_event(state, sender="EXECUTION_ENVIRONMENT", recipient="AGENT", tool_name=self.tool_name, arguments=args)
        return ToolExecutionResult(success=True, observation={"tool_trace": event["tool_trace"]}, state_changed=True)


_GENERIC_TOOL_NAMES = [
    "convert_currency",
    "unit_conversion",
    "get_current_timestamp",
    "timestamp_diff",
    "timestamp_to_datetime_info",
    "datetime_info_to_timestamp",
    "shift_timestamp",
    "search_location_around_lat_lon",
    "search_lat_lon",
    "search_holiday",
    "search_stock",
    "search_weather_around_lat_lon",
    "calculate_lat_lon_distance",
    "seconds_to_hours_minutes_seconds",
]


TOOLSANDBOX_TOOLS: dict[str, ToolSpec] = {
    "add_contact": AddContactTool(),
    "modify_contact": ModifyContactTool(),
    "remove_contact": RemoveContactTool(),
    "search_contacts": SearchContactsTool(),
    "set_wifi_status": SetSettingTool("set_wifi_status", "wifi"),
    "get_wifi_status": GetSettingTool("get_wifi_status", "wifi"),
    "set_cellular_service_status": SetSettingTool("set_cellular_service_status", "cellular"),
    "get_cellular_service_status": GetSettingTool("get_cellular_service_status", "cellular"),
    "set_location_service_status": SetSettingTool("set_location_service_status", "location_service"),
    "get_location_service_status": GetSettingTool("get_location_service_status", "location_service"),
    "set_low_battery_mode_status": SetSettingTool("set_low_battery_mode_status", "low_battery_mode"),
    "get_low_battery_mode_status": GetSettingTool("get_low_battery_mode_status", "low_battery_mode"),
    "get_current_location": GetCurrentLocationTool(),
    "add_reminder": AddReminderTool(),
    "modify_reminder": ModifyReminderTool(),
    "remove_reminder": RemoveReminderTool(),
    "search_reminder": SearchReminderTool(),
    "send_message_with_phone_number": SendMessageTool(),
    "search_messages": SearchMessagesTool(),
    "end_conversation": EndConversationTool(),
}
TOOLSANDBOX_TOOLS.update({name: GenericToolTraceTool(name) for name in _GENERIC_TOOL_NAMES})
