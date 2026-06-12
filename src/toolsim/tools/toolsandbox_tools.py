"""ToolSandbox-compatible tools backed by a local runtime.

The implementation mirrors the core official ToolSandbox semantics for
settings, contacts, messaging, and reminders while staying inside AgentInferKit's
deterministic WorldState execution model.
"""

from __future__ import annotations

from typing import Any

from toolsim.core.tool_spec import ExecutionContext, ToolExecutionResult, ToolMetadata, ToolSpec
from toolsim.tools.toolsandbox_runtime import (
    CONTACT,
    MESSAGE,
    REMINDER,
    SANDBOX,
    SETTING,
    call_toolsandbox_tool,
    record_end_conversation,
)


def _state_and_backend(state_or_context: Any) -> tuple[Any, Any]:
    if isinstance(state_or_context, ExecutionContext):
        return state_or_context.state, state_or_context.backend
    return state_or_context, None


def _execute_toolsandbox_tool(state_or_context: Any, tool_name: str, args: dict[str, Any]) -> ToolExecutionResult:
    state, backend = _state_and_backend(state_or_context)
    if backend is not None and hasattr(backend, "call_toolsandbox_tool"):
        result = backend.call_toolsandbox_tool(state, tool_name, args)
    else:
        result = call_toolsandbox_tool(state, tool_name, args)
    observation = _observation_for_tool(tool_name, result["observation"])
    return ToolExecutionResult(
        success=bool(result["success"]),
        error=result["error"],
        observation=observation,
        state_changed=bool(result["state_changed"]),
        metadata={"toolsandbox": True},
    )


def _observation_for_tool(tool_name: str, observation: dict[str, Any]) -> dict[str, Any]:
    output = observation.get("output")
    exception = observation.get("exception")
    base = {"tool_name": tool_name, **observation}
    if exception is not None:
        return base
    if tool_name in {"add_contact", "modify_contact"}:
        return {**base, "contact": output if isinstance(output, dict) else output}
    if tool_name == "remove_contact":
        return {**base, "removed": True}
    if tool_name == "search_contacts":
        hits = output if isinstance(output, list) else []
        return {**base, "hits": hits, "count": len(hits)}
    if tool_name.startswith("set_") or tool_name.startswith("get_"):
        field_name = _setting_field_for_tool(tool_name)
        return {**base, "value": output, field_name: output}
    if tool_name in {"add_reminder", "modify_reminder"}:
        return {**base, "reminder": output if isinstance(output, dict) else output}
    if tool_name == "remove_reminder":
        return {**base, "removed": True}
    if tool_name == "search_reminder":
        hits = output if isinstance(output, list) else []
        return {**base, "hits": hits, "count": len(hits)}
    if tool_name == "send_message_with_phone_number":
        return {**base, "message": output if isinstance(output, dict) else output}
    if tool_name == "search_messages":
        hits = output if isinstance(output, list) else []
        return {**base, "hits": hits, "count": len(hits)}
    return base


def _setting_field_for_tool(tool_name: str) -> str:
    mapping = {
        "set_wifi_status": "wifi",
        "get_wifi_status": "wifi",
        "set_cellular_service_status": "cellular",
        "get_cellular_service_status": "cellular",
        "set_location_service_status": "location_service",
        "get_location_service_status": "location_service",
        "set_low_battery_mode_status": "low_battery_mode",
        "get_low_battery_mode_status": "low_battery_mode",
    }
    return mapping.get(tool_name, "value")


class ToolSandboxTool(ToolSpec):
    tool_name = ""
    domain = "toolsandbox"

    def execute(self, state_or_context: Any, args: dict[str, Any]) -> ToolExecutionResult:
        return _execute_toolsandbox_tool(state_or_context, self.tool_name, args)


class AddContactTool(ToolSandboxTool):
    tool_name = "add_contact"
    metadata = ToolMetadata(name=tool_name, version="0.2", domain="toolsandbox.contacts")


class ModifyContactTool(ToolSandboxTool):
    tool_name = "modify_contact"
    metadata = ToolMetadata(name=tool_name, version="0.2", domain="toolsandbox.contacts")


class RemoveContactTool(ToolSandboxTool):
    tool_name = "remove_contact"
    metadata = ToolMetadata(name=tool_name, version="0.2", domain="toolsandbox.contacts")


class SearchContactsTool(ToolSandboxTool):
    tool_name = "search_contacts"
    metadata = ToolMetadata(name=tool_name, version="0.2", domain="toolsandbox.contacts")


class SetSettingTool(ToolSandboxTool):
    def __init__(self, tool_name: str, field_name: str) -> None:
        self.tool_name = tool_name
        self.field_name = field_name
        self.metadata = ToolMetadata(name=tool_name, version="0.2", domain="toolsandbox.settings")


class GetSettingTool(ToolSandboxTool):
    def __init__(self, tool_name: str, field_name: str) -> None:
        self.tool_name = tool_name
        self.field_name = field_name
        self.metadata = ToolMetadata(name=tool_name, version="0.2", domain="toolsandbox.settings")


class GetCurrentLocationTool(ToolSandboxTool):
    tool_name = "get_current_location"
    metadata = ToolMetadata(name=tool_name, version="0.2", domain="toolsandbox.settings")


class AddReminderTool(ToolSandboxTool):
    tool_name = "add_reminder"
    metadata = ToolMetadata(name=tool_name, version="0.2", domain="toolsandbox.reminders")


class ModifyReminderTool(ToolSandboxTool):
    tool_name = "modify_reminder"
    metadata = ToolMetadata(name=tool_name, version="0.2", domain="toolsandbox.reminders")


class RemoveReminderTool(ToolSandboxTool):
    tool_name = "remove_reminder"
    metadata = ToolMetadata(name=tool_name, version="0.2", domain="toolsandbox.reminders")


class SearchReminderTool(ToolSandboxTool):
    tool_name = "search_reminder"
    metadata = ToolMetadata(name=tool_name, version="0.2", domain="toolsandbox.reminders")


class SendMessageTool(ToolSandboxTool):
    tool_name = "send_message_with_phone_number"
    metadata = ToolMetadata(name=tool_name, version="0.2", domain="toolsandbox.messaging")


class SearchMessagesTool(ToolSandboxTool):
    tool_name = "search_messages"
    metadata = ToolMetadata(name=tool_name, version="0.2", domain="toolsandbox.messaging")


class EndConversationTool(ToolSpec):
    tool_name = "end_conversation"
    metadata = ToolMetadata(name=tool_name, version="0.2", domain="toolsandbox.sandbox")

    def execute(self, state_or_context: Any, args: dict[str, Any]) -> ToolExecutionResult:
        state, backend = _state_and_backend(state_or_context)
        if backend is not None and hasattr(backend, "record_toolsandbox_end_conversation"):
            result = backend.record_toolsandbox_end_conversation(state, args)
        else:
            result = record_end_conversation(state, args)
        return ToolExecutionResult(
            success=bool(result["success"]),
            error=result["error"],
            observation=result["observation"],
            state_changed=bool(result["state_changed"]),
            metadata={"toolsandbox": True},
        )


class GenericToolTraceTool(ToolSpec):
    """Track a ToolSandbox helper tool call without external side effects."""

    def __init__(self, tool_name: str) -> None:
        self.tool_name = tool_name
        self.metadata = ToolMetadata(name=tool_name, version="0.1", domain="toolsandbox.helper")

    def execute(self, state_or_context: Any, args: dict[str, Any]) -> ToolExecutionResult:
        state, _ = _state_and_backend(state_or_context)
        result = call_toolsandbox_tool(state, self.tool_name, args) if self.tool_name == "end_conversation" else None
        if result is not None:
            return ToolExecutionResult(
                success=bool(result["success"]),
                error=result["error"],
                observation=result["observation"],
                state_changed=bool(result["state_changed"]),
                metadata={"toolsandbox": True},
            )
        from toolsim.tools.toolsandbox_runtime import _record_sandbox_event

        event = _record_sandbox_event(
            state,
            sender="EXECUTION_ENVIRONMENT",
            recipient="AGENT",
            tool_name=self.tool_name,
            arguments=args,
        )
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


__all__ = [
    "CONTACT",
    "REMINDER",
    "MESSAGE",
    "SETTING",
    "SANDBOX",
    "TOOLSANDBOX_TOOLS",
    "AddContactTool",
    "ModifyContactTool",
    "RemoveContactTool",
    "SearchContactsTool",
    "SetSettingTool",
    "GetSettingTool",
    "GetCurrentLocationTool",
    "AddReminderTool",
    "ModifyReminderTool",
    "RemoveReminderTool",
    "SearchReminderTool",
    "SendMessageTool",
    "SearchMessagesTool",
    "EndConversationTool",
]
