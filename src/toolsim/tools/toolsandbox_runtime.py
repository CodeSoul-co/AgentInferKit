"""ToolSandbox-compatible runtime for local live-like execution."""

from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Any

from toolsim.core.world_state import WorldState

CONTACT = "contact"
REMINDER = "reminder"
MESSAGE = "messaging"
SETTING = "setting"
SANDBOX = "sandbox"

TOOLSANDBOX_RUNTIME_NAME = "setting_contact_messaging_reminder"
TOOLSANDBOX_DATABASE_ENTITY_TYPES = (SETTING, CONTACT, MESSAGE, REMINDER, SANDBOX)

_NOT_GIVEN = object()
_PHONE_RE = re.compile(r"^\+?[0-9][0-9\s().-]{1,31}$")


def ensure_toolsandbox_state(state: WorldState) -> None:
    """Seed the ToolSandbox-style databases used by the local runtime."""
    state.entities.setdefault(CONTACT, {})
    state.entities.setdefault(REMINDER, {})
    state.entities.setdefault(MESSAGE, {})
    state.entities.setdefault(SANDBOX, {})
    settings = state.entities.setdefault(SETTING, {})
    device = settings.setdefault("device", {})
    device.setdefault("wifi", False)
    device.setdefault("cellular", True)
    device.setdefault("location_service", True)
    device.setdefault("low_battery_mode", False)
    device.setdefault("latitude", 37.3349)
    device.setdefault("longitude", -122.0090)
    state.resources.setdefault("toolsandbox_source", "apple/ToolSandbox")
    state.policies.setdefault("backend", {})
    state.policies["backend"]["toolsandbox_runtime"] = TOOLSANDBOX_RUNTIME_NAME


def persist_toolsandbox_databases(state: WorldState, database_dir: str | Path) -> None:
    """Persist ToolSandbox-style databases as session artifacts."""
    path = Path(database_dir)
    path.mkdir(parents=True, exist_ok=True)
    for entity_type, filename in (
        (SETTING, "Setting.json"),
        (CONTACT, "Contact.json"),
        (MESSAGE, "Messaging.json"),
        (REMINDER, "Reminder.json"),
        (SANDBOX, "Sandbox.json"),
    ):
        (path / filename).write_text(
            json.dumps(state.entities.get(entity_type, {}), ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )


def call_toolsandbox_tool(state: WorldState, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Run one supported ToolSandbox tool and return a normalized result."""
    ensure_toolsandbox_state(state)
    try:
        output, state_changed = _dispatch_tool(state, tool_name, args)
    except Exception as exc:
        _record_sandbox_event(
            state,
            sender="EXECUTION_ENVIRONMENT",
            recipient="AGENT",
            tool_name=tool_name,
            arguments=args,
            exception=str(exc),
        )
        return {
            "success": False,
            "state_changed": True,
            "observation": {"tool_name": tool_name, "input": dict(args), "output": None, "exception": str(exc)},
            "error": str(exc),
        }

    _record_sandbox_event(
        state,
        sender="EXECUTION_ENVIRONMENT",
        recipient="AGENT",
        tool_name=tool_name,
        arguments=args,
        exception=None,
    )
    return {
        "success": True,
        "state_changed": True if tool_name != "end_conversation" else state_changed,
        "observation": {"tool_name": tool_name, "input": dict(args), "output": output, "exception": None},
        "error": None,
    }


def record_end_conversation(state: WorldState, args: dict[str, Any]) -> dict[str, Any]:
    ensure_toolsandbox_state(state)
    content = args.get("content")
    if content:
        _record_sandbox_event(state, sender="AGENT", recipient=args.get("recipient", "USER"), content=content)
    event = _record_sandbox_event(
        state,
        sender="AGENT",
        recipient="END",
        tool_name="end_conversation",
        arguments=args,
    )
    return {
        "success": True,
        "state_changed": True,
        "observation": {"ended": True, "event": event},
        "error": None,
    }


def _dispatch_tool(state: WorldState, tool_name: str, args: dict[str, Any]) -> tuple[Any, bool]:
    if tool_name == "add_contact":
        return _add_contact(state, args), True
    if tool_name == "modify_contact":
        _modify_contact(state, args)
        return None, True
    if tool_name == "remove_contact":
        _remove_contact(state, args)
        return None, True
    if tool_name == "search_contacts":
        return _search_contacts(state, args), False
    if tool_name in {"set_wifi_status", "set_cellular_service_status", "set_location_service_status", "set_low_battery_mode_status"}:
        _set_setting(state, _setting_field_for_tool(tool_name), _setting_value_for_args(args, _setting_field_for_tool(tool_name)))
        return None, True
    if tool_name in {"get_wifi_status", "get_cellular_service_status", "get_location_service_status", "get_low_battery_mode_status"}:
        return _get_setting(state, _setting_field_for_tool(tool_name)), False
    if tool_name == "get_current_location":
        return _get_current_location(state), False
    if tool_name == "add_reminder":
        return _add_reminder(state, args), True
    if tool_name == "modify_reminder":
        _modify_reminder(state, args)
        return None, True
    if tool_name == "remove_reminder":
        _remove_reminder(state, args)
        return None, True
    if tool_name == "search_reminder":
        return _search_reminder(state, args), False
    if tool_name == "send_message_with_phone_number":
        return _send_message_with_phone_number(state, args), True
    if tool_name == "search_messages":
        return _search_messages(state, args), False
    if tool_name == "end_conversation":
        return record_end_conversation(state, args)["observation"], True
    raise Exception(f"Unsupported ToolSandbox tool: {tool_name}")


def _settings(state: WorldState) -> dict[str, Any]:
    ensure_toolsandbox_state(state)
    return dict(state.entities[SETTING]["device"])


def _write_settings(state: WorldState, settings: dict[str, Any]) -> None:
    state.set_entity(SETTING, "device", settings)


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
    return mapping[tool_name]


def _setting_value_for_args(args: dict[str, Any], field_name: str) -> bool:
    for key in (field_name, "on", "status", "enabled"):
        if key in args:
            return bool(args[key])
    raise Exception(f"Missing boolean argument for {field_name}")


def _get_setting(state: WorldState, field_name: str) -> bool:
    settings = _settings(state)
    if field_name not in settings:
        raise KeyError(f"{field_name} is not a boolean column")
    return bool(settings[field_name])


def _set_setting(state: WorldState, field_name: str, on: bool) -> None:
    settings = _settings(state)
    if field_name not in settings:
        raise KeyError(f"{field_name} is not a boolean column")
    if field_name in {"cellular", "wifi", "location_service"} and on and bool(settings.get("low_battery_mode")):
        label = "Wifi" if field_name == "wifi" else "Cellular service" if field_name == "cellular" else "Location service"
        raise PermissionError(f"{label} cannot be turned on in low battery mode")
    if bool(settings[field_name]) == on:
        raise ValueError(f"{field_name} already {('disabled', 'enabled')[int(on)]}")
    settings[field_name] = on
    if field_name == "low_battery_mode" and on:
        for dependent in ("cellular", "wifi", "location_service"):
            settings[dependent] = False
    settings["updated_at"] = state.now()
    _write_settings(state, settings)


def _get_current_location(state: WorldState) -> dict[str, float]:
    settings = _settings(state)
    if not bool(settings.get("location_service")):
        raise PermissionError("Location service is not enabled.")
    return {"latitude": float(settings["latitude"]), "longitude": float(settings["longitude"])}


def _add_contact(state: WorldState, args: dict[str, Any]) -> str:
    phone_number = args.get("phone_number")
    _validate_phone_number(phone_number)
    is_self = bool(args.get("is_self", False))
    if is_self and _search_contacts(state, {"is_self": True}):
        raise Exception("Self entry already exists. Cannot add another one.")
    person_id = str(args.get("person_id") or _new_id("person"))
    state.set_entity(CONTACT, person_id, {
        "person_id": person_id,
        "name": args.get("name"),
        "phone_number": phone_number,
        "relationship": args.get("relationship"),
        "is_self": is_self,
        "sandbox_message_index": args.get("sandbox_message_index"),
        "created_at": state.now(),
        "updated_at": state.now(),
    })
    return person_id


def _modify_contact(state: WorldState, args: dict[str, Any]) -> None:
    update_fields = {field: args[field] for field in ("name", "phone_number", "relationship", "is_self") if field in args}
    if not update_fields:
        raise ValueError("No update information given. At least one new field should be provided among [name, phone_number, relationship, is_self] in order to modify contact")
    if "phone_number" in update_fields:
        _validate_phone_number(update_fields["phone_number"])
    person_id = args.get("person_id")
    if not person_id:
        raise Exception("person_id is required to modify contact")
    contacts = state.entities.get(CONTACT, {})
    if person_id not in contacts:
        raise Exception(f"No db entry matching person_id='{person_id}' found")
    if update_fields.get("is_self") is True:
        for existing_id, contact in contacts.items():
            if existing_id != person_id and contact.get("is_self"):
                raise Exception("Self entry already exists. Cannot add another one.")
    updated = dict(contacts[person_id])
    updated.update(update_fields)
    updated["updated_at"] = state.now()
    state.set_entity(CONTACT, str(person_id), updated)


def _remove_contact(state: WorldState, args: dict[str, Any]) -> None:
    person_id = args.get("person_id")
    if not person_id:
        raise Exception("person_id is required to remove contact")
    if not state.delete_entity(CONTACT, str(person_id)):
        raise Exception(f"No db entry matching person_id='{person_id}' found")


def _search_contacts(state: WorldState, args: dict[str, Any]) -> list[dict[str, Any]]:
    criteria = {key: value for key, value in args.items() if value is not None}
    if not criteria:
        raise ValueError("At least one search argument should be provided")
    hits = []
    for contact in state.entities.get(CONTACT, {}).values():
        if _matches_contact(contact, criteria):
            hits.append(dict(contact))
    return hits


def _matches_contact(contact: dict[str, Any], criteria: dict[str, Any]) -> bool:
    for key, expected in criteria.items():
        if key == "query":
            query = str(expected).lower()
            haystack = " ".join(str(contact.get(field) or "") for field in ("name", "phone_number", "relationship")).lower()
            if query not in haystack:
                return False
        elif key in {"name", "relationship"}:
            if not _fuzzy_contains(contact.get(key), expected):
                return False
        elif contact.get(key) != expected:
            return False
    return True


def _add_reminder(state: WorldState, args: dict[str, Any]) -> str:
    reminder_timestamp = _validate_timestamp(args.get("reminder_timestamp"), "reminder_timestamp", required=True)
    latitude = _validate_latitude(args.get("latitude"))
    longitude = _validate_longitude(args.get("longitude"))
    reminder_id = str(args.get("reminder_id") or _new_id("reminder"))
    state.set_entity(REMINDER, reminder_id, {
        "reminder_id": reminder_id,
        "content": args.get("content"),
        "creation_timestamp": state.now(),
        "reminder_timestamp": reminder_timestamp,
        "latitude": latitude,
        "longitude": longitude,
        "sandbox_message_index": args.get("sandbox_message_index"),
        "updated_at": state.now(),
    })
    return reminder_id


def _modify_reminder(state: WorldState, args: dict[str, Any]) -> None:
    reminder_id = args.get("reminder_id")
    if not reminder_id:
        raise Exception("reminder_id is required to modify reminder")
    reminder = state.get_entity(REMINDER, str(reminder_id))
    if reminder is None:
        raise Exception(f"No db entry matching reminder_id='{reminder_id}' found")
    update_fields = {field: args[field] for field in ("content", "reminder_timestamp", "latitude", "longitude") if field in args}
    if not update_fields:
        raise ValueError("No update information given. At least one new field should be provided among [content, reminder_timestamp, latitude, longitude] in order to modify reminder")
    if "reminder_timestamp" in update_fields:
        update_fields["reminder_timestamp"] = _validate_timestamp(update_fields["reminder_timestamp"], "reminder_timestamp", required=True)
    if "latitude" in update_fields:
        update_fields["latitude"] = _validate_latitude(update_fields["latitude"])
    if "longitude" in update_fields:
        update_fields["longitude"] = _validate_longitude(update_fields["longitude"])
    updated = dict(reminder)
    updated.update(update_fields)
    updated["creation_timestamp"] = state.now()
    updated["updated_at"] = state.now()
    state.set_entity(REMINDER, str(reminder_id), updated)


def _remove_reminder(state: WorldState, args: dict[str, Any]) -> None:
    reminder_id = args.get("reminder_id")
    if not reminder_id:
        raise Exception("reminder_id is required to remove reminder")
    if not state.delete_entity(REMINDER, str(reminder_id)):
        raise Exception(f"No db entry matching reminder_id='{reminder_id}' found")


def _search_reminder(state: WorldState, args: dict[str, Any]) -> list[dict[str, Any]]:
    if not any(value is not None for value in args.values()):
        raise ValueError("At least one search argument should be provided")
    hits = []
    for reminder in state.entities.get(REMINDER, {}).values():
        if _matches_reminder(reminder, args):
            hits.append(dict(reminder))
    return hits


def _matches_reminder(reminder: dict[str, Any], criteria: dict[str, Any]) -> bool:
    for key, expected in criteria.items():
        if expected is None:
            continue
        if key in {"content", "query"}:
            if not _fuzzy_contains(reminder.get("content"), expected):
                return False
        elif key.endswith("_lowerbound"):
            field = key.removesuffix("_lowerbound")
            if float(reminder.get(field, 0.0)) < float(expected):
                return False
        elif key.endswith("_upperbound"):
            field = key.removesuffix("_upperbound")
            if float(reminder.get(field, 0.0)) > float(expected):
                return False
        elif reminder.get(key) != expected:
            return False
    return True


def _send_message_with_phone_number(state: WorldState, args: dict[str, Any]) -> str:
    phone_number = args.get("phone_number", args.get("recipient_phone_number"))
    _validate_phone_number(phone_number)
    if not _get_setting(state, "cellular"):
        raise ConnectionError("Cellular service is not enabled")
    self_contacts = _search_contacts(state, {"is_self": True})
    if len(self_contacts) != 1:
        raise Exception(f"1 and only 1 self entry should exist in contacts database, instead found {len(self_contacts)}")
    recipient_data = _search_contacts(state, {"phone_number": phone_number})
    recipient_person_id = None if len(recipient_data) == 0 else recipient_data[0]["person_id"]
    message_id = str(args.get("message_id") or _new_id("message"))
    state.set_entity(MESSAGE, message_id, {
        "message_id": message_id,
        "sender_person_id": self_contacts[0]["person_id"],
        "sender_phone_number": self_contacts[0]["phone_number"],
        "recipient_person_id": recipient_person_id,
        "recipient_phone_number": phone_number,
        "content": args.get("content"),
        "creation_timestamp": state.now(),
        "sandbox_message_index": args.get("sandbox_message_index"),
    })
    return message_id


def _search_messages(state: WorldState, args: dict[str, Any]) -> list[dict[str, Any]]:
    if not any(value is not None for value in args.values()):
        raise ValueError("At least one search argument should be provided")
    hits = []
    for message in state.entities.get(MESSAGE, {}).values():
        if _matches_message(message, args):
            hits.append(dict(message))
    return hits


def _matches_message(message: dict[str, Any], criteria: dict[str, Any]) -> bool:
    for key, expected in criteria.items():
        if expected is None:
            continue
        if key in {"content", "query"}:
            if not _fuzzy_contains(message.get("content"), expected):
                return False
        elif key.endswith("_lowerbound"):
            field = key.removesuffix("_lowerbound")
            if float(message.get(field, 0.0)) < float(expected):
                return False
        elif key.endswith("_upperbound"):
            field = key.removesuffix("_upperbound")
            if float(message.get(field, 0.0)) > float(expected):
                return False
        else:
            mapped_key = "recipient_phone_number" if key == "phone_number" else key
            if message.get(mapped_key) != expected:
                return False
    return True


def _record_sandbox_event(
    state: WorldState,
    *,
    sender: str,
    recipient: str,
    content: str | None = None,
    tool_name: str | None = None,
    arguments: dict[str, Any] | None = None,
    exception: str | None = None,
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
        "tool_call_exception": exception,
        "tool_trace": json.dumps({"tool_name": tool_name, "arguments": arguments or {}}, sort_keys=True) if tool_name else None,
        "visible_to": [recipient],
        "created_at": state.now(),
    }
    state.set_entity(SANDBOX, event_id, event)
    return event


def _validate_phone_number(value: Any) -> None:
    if value is None:
        return
    if not isinstance(value, str) or not _PHONE_RE.match(value):
        raise ValueError(f"Invalid phone number: {value!r}")


def _validate_timestamp(value: Any, field_name: str, *, required: bool) -> float | None:
    if value is None:
        if required:
            raise ValueError(f"{field_name} is required")
        return None
    if not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a number")
    return float(value)


def _validate_latitude(value: Any) -> float | None:
    if value is None:
        return None
    if not isinstance(value, (int, float)) or not -90 <= float(value) <= 90:
        raise ValueError("latitude must be between -90 and 90")
    return float(value)


def _validate_longitude(value: Any) -> float | None:
    if value is None:
        return None
    if not isinstance(value, (int, float)) or not -180 <= float(value) <= 180:
        raise ValueError("longitude must be between -180 and 180")
    return float(value)


def _fuzzy_contains(actual: Any, expected: Any) -> bool:
    if expected is None:
        return True
    return str(expected).lower() in str(actual or "").lower()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"
