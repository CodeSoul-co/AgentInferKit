from __future__ import annotations

from typing import Any, Dict, List, Optional

from toolsim.backends.base import BaseBackend
from toolsim.core.trace_state import PendingEffect, TraceState
from toolsim.tools.apibank_runtime import APIBANK_VERIFICATION_CODE, ensure_apibank_state
from toolsim.tools.toolsandbox_runtime import (
    CONTACT,
    MESSAGE,
    REMINDER,
    SANDBOX,
    SETTING,
    ensure_toolsandbox_state,
    _record_sandbox_event,
)


class MockBackend(BaseBackend):
    """In-memory backend that delegates directly to TraceState."""

    def get_backend_name(self) -> str:
        return "mock"

    def create_state(self) -> TraceState:
        return TraceState()

    def clone_state(self, state: TraceState) -> TraceState:
        return TraceState.from_dict(state.to_dict())

    def snapshot_state(self, state: TraceState, label: Optional[str] = None) -> str:
        return state.create_snapshot(label)

    def rollback_state(self, state: TraceState, snapshot_id: str) -> bool:
        return state.rollback_to(snapshot_id)

    def get_entity(self, state: TraceState, entity_type: str, entity_id: str) -> Optional[Dict[str, Any]]:
        return state.get_entity(entity_type, entity_id)

    def set_entity(self, state: TraceState, entity_type: str, entity_id: str, value: Dict[str, Any]) -> None:
        state.set_entity(entity_type, entity_id, value)

    def delete_entity(self, state: TraceState, entity_type: str, entity_id: str) -> bool:
        return state.delete_entity(entity_type, entity_id)

    def list_entities(self, state: TraceState, entity_type: str) -> List[Dict[str, Any]]:
        return list(state.entities.get(entity_type, {}).values())

    def schedule_effect(self, state: TraceState, effect: PendingEffect) -> None:
        state.schedule_effect(effect)

    def list_pending_effects(self, state: TraceState, status: Optional[str] = None) -> List[PendingEffect]:
        return state.list_pending_effects(status=status)

    def call_apibank_api(self, state: TraceState, api_name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Optimistically execute API-Bank-style calls for baseline mock runs.

        Mock intentionally models a permissive state machine: malformed
        credentials, missing rows, or invalid timestamps do not block the final
        mutation. Sandbox and live-like backends provide the strict semantics.
        """
        ensure_apibank_state(state)
        input_parameters = dict(args)
        output: Any = {"status": "success"}
        state_changed = False

        if api_name == "CheckToken":
            output = {"username": self._username_for_token(state, str(args.get("token", "")))}
        elif api_name == "GetUserToken":
            username = str(args.get("username") or "foo")
            account = state.get_entity("account", username) or {"token": "mock-token"}
            output = {"token": account.get("token", "mock-token")}
        elif api_name == "ModifyPassword":
            username = self._username_for_token(state, str(args.get("token", "")))
            account = state.get_entity("account", username) or {"username": username, "token": args.get("token", "mock-token")}
            updated = dict(account)
            updated["password"] = args.get("new_password")
            state.set_entity("account", username, updated)
            state_changed = True
        elif api_name == "ForgotPassword":
            output, state_changed = self._mock_forgot_password(state, args)
        elif api_name in {"AddAgenda", "ModifyAgenda"}:
            self._upsert_agenda(state, args)
            state_changed = True
        elif api_name == "QueryAgenda":
            output = self._query_first(state, "agenda", args, ("content", "time"))
        elif api_name in {"AddMeeting", "ModifyMeeting"}:
            self._upsert_meeting(state, args)
            state_changed = True
        elif api_name == "QueryMeeting":
            output = self._query_first(state, "meeting", args, ("meeting_topic", "start_time"))

        return {
            "success": True,
            "state_changed": state_changed,
            "observation": {
                "api_name": api_name,
                "input": input_parameters,
                "output": output,
                "exception": None,
            },
            "error": None,
        }

    def call_toolsandbox_tool(self, state: TraceState, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Optimistically execute ToolSandbox-style tools for mock baselines."""
        ensure_toolsandbox_state(state)
        output: Any = None
        state_changed = True

        if tool_name == "add_contact":
            output = self._upsert_contact(state, args)
        elif tool_name == "modify_contact":
            output = self._upsert_contact(state, args)
        elif tool_name == "remove_contact":
            state.delete_entity(CONTACT, str(args.get("person_id", "")))
        elif tool_name == "search_contacts":
            output = self._match_records(state, CONTACT, args)
            state_changed = False
        elif tool_name.startswith("set_"):
            field_name = _setting_field_for_tool(tool_name)
            settings = dict(state.entities[SETTING]["device"])
            settings[field_name] = bool(args.get(field_name, args.get("on", args.get("status", args.get("enabled", True)))))
            state.set_entity(SETTING, "device", settings)
        elif tool_name.startswith("get_"):
            field_name = _setting_field_for_tool(tool_name)
            output = state.entities[SETTING]["device"].get(field_name)
            state_changed = False
        elif tool_name == "get_current_location":
            settings = state.entities[SETTING]["device"]
            output = {"latitude": settings.get("latitude"), "longitude": settings.get("longitude")}
            state_changed = False
        elif tool_name == "add_reminder":
            output = self._upsert_reminder(state, args)
        elif tool_name == "modify_reminder":
            output = self._upsert_reminder(state, args)
        elif tool_name == "remove_reminder":
            state.delete_entity(REMINDER, str(args.get("reminder_id", "")))
        elif tool_name == "search_reminder":
            output = self._match_records(state, REMINDER, args)
            state_changed = False
        elif tool_name == "send_message_with_phone_number":
            output = self._send_message(state, args)
        elif tool_name == "search_messages":
            output = self._match_records(state, MESSAGE, args)
            state_changed = False
        elif tool_name == "end_conversation":
            return self.record_toolsandbox_end_conversation(state, args)

        _record_sandbox_event(
            state,
            sender="EXECUTION_ENVIRONMENT",
            recipient="AGENT",
            tool_name=tool_name,
            arguments=args,
        )
        return {
            "success": True,
            "state_changed": True if tool_name != "end_conversation" else state_changed,
            "observation": {"tool_name": tool_name, "input": dict(args), "output": output, "exception": None},
            "error": None,
        }

    def record_toolsandbox_end_conversation(self, state: TraceState, args: dict[str, Any]) -> dict[str, Any]:
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

    def _username_for_token(self, state: TraceState, token: str) -> str:
        for username, account in state.entities.get("account", {}).items():
            if account.get("token") == token:
                return str(username)
        return "foo"

    def _mock_forgot_password(self, state: TraceState, args: dict[str, Any]) -> tuple[Any, bool]:
        if args.get("status") == "Forgot Password":
            username = str(args.get("username") or "foo")
            state.set_entity("password_reset", "current", {
                "username": username,
                "verification_code": APIBANK_VERIFICATION_CODE,
                "status": "issued",
                "consumed": False,
            })
            return APIBANK_VERIFICATION_CODE, True
        username = str((state.get_entity("password_reset", "current") or {}).get("username", args.get("username", "foo")))
        account = state.get_entity("account", username) or {"username": username, "token": "mock-token"}
        updated = dict(account)
        updated["password"] = args.get("new_password")
        state.set_entity("account", username, updated)
        state.set_entity("password_reset", "current", {
            "username": username,
            "verification_code": args.get("verification_code", APIBANK_VERIFICATION_CODE),
            "status": "consumed",
            "consumed": True,
        })
        return "success", True

    def _upsert_agenda(self, state: TraceState, args: dict[str, Any]) -> None:
        entity_id = next(iter(state.entities.get("agenda", {})), "1")
        state.set_entity("agenda", str(entity_id), {
            "username": self._username_for_token(state, str(args.get("token", ""))),
            "content": args.get("content"),
            "time": args.get("normalized_time", args.get("time")),
            "location": args.get("location"),
        })

    def _upsert_meeting(self, state: TraceState, args: dict[str, Any]) -> None:
        entity_id = next(iter(state.entities.get("meeting", {})), "0")
        state.set_entity("meeting", str(entity_id), {
            "username": self._username_for_token(state, str(args.get("token", ""))),
            "meeting_topic": args.get("meeting_topic"),
            "start_time": args.get("start_time"),
            "end_time": args.get("end_time"),
            "location": args.get("location"),
            "attendees": list(args.get("attendees", [])),
        })

    def _query_first(self, state: TraceState, entity_type: str, args: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any] | None:
        for record in state.entities.get(entity_type, {}).values():
            if any(args.get(key) and record.get(key) == args.get(key) for key in keys):
                return dict(record)
        return next((dict(record) for record in state.entities.get(entity_type, {}).values()), None)

    def _upsert_contact(self, state: TraceState, args: dict[str, Any]) -> str:
        person_id = str(args.get("person_id") or f"mock_contact_{len(state.entities.get(CONTACT, {})) + 1}")
        existing = state.get_entity(CONTACT, person_id) or {}
        updated = {
            "person_id": person_id,
            "name": args.get("name", existing.get("name")),
            "phone_number": args.get("phone_number", existing.get("phone_number")),
            "relationship": args.get("relationship", existing.get("relationship")),
            "is_self": bool(args.get("is_self", existing.get("is_self", False))),
        }
        state.set_entity(CONTACT, person_id, updated)
        return person_id

    def _upsert_reminder(self, state: TraceState, args: dict[str, Any]) -> str:
        reminder_id = str(args.get("reminder_id") or f"mock_reminder_{len(state.entities.get(REMINDER, {})) + 1}")
        existing = state.get_entity(REMINDER, reminder_id) or {}
        updated = dict(existing)
        updated.update(args)
        updated["reminder_id"] = reminder_id
        state.set_entity(REMINDER, reminder_id, updated)
        return reminder_id

    def _send_message(self, state: TraceState, args: dict[str, Any]) -> str:
        message_id = str(args.get("message_id") or f"mock_message_{len(state.entities.get(MESSAGE, {})) + 1}")
        phone_number = args.get("phone_number", args.get("recipient_phone_number"))
        state.set_entity(MESSAGE, message_id, {
            "message_id": message_id,
            "recipient_phone_number": phone_number,
            "content": args.get("content"),
        })
        return message_id

    def _match_records(self, state: TraceState, entity_type: str, args: dict[str, Any]) -> list[dict[str, Any]]:
        criteria = {key: value for key, value in args.items() if value is not None}
        if not criteria:
            return [dict(record) for record in state.entities.get(entity_type, {}).values()]
        hits = []
        for record in state.entities.get(entity_type, {}).values():
            if all(_loosely_matches(record.get(key), value) for key, value in criteria.items()):
                hits.append(dict(record))
        return hits


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


def _loosely_matches(actual: Any, expected: Any) -> bool:
    if expected is None:
        return True
    return str(expected).lower() in str(actual or "").lower()
