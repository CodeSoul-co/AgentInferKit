"""Small API-Bank-compatible runtime used by live-like experiments."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from toolsim.core.world_state import WorldState


APIBANK_ACCOUNT_DATABASE: dict[str, dict[str, str]] = {
    "JohnDoe": {"password": "pass123", "token": "a9s8d7f6g5h4j3k2l1", "email": "johndoe@example.com"},
    "JaneSmith": {"password": "password", "token": "o8i7u6y5t4r3e2w1q0", "email": "janesmith@example.com"},
    "testuser": {"password": "testpass", "token": "p9o8i7u6y5t4k3e2w1q", "email": "testuser@example.com"},
    "foo": {"password": "bar", "token": "z9x8c7v6b5n4m3q2w1", "email": "foo@example.com"},
    "newuser": {"password": "newpass", "token": "l9k8j7h6g5f4d3s2a1", "email": "newuser@example.com"},
    "admin": {"password": "adminpass", "token": "m9n8b7v6c5x4z3a2s1", "email": "admin@example.com"},
    "user1": {"password": "user1pass", "token": "n9m8k7j6h5g4f3d2s1a0", "email": "user1@example.com"},
    "user2": {"password": "user2pass", "token": "o9i8u7y6t5r4e3w2q1", "email": "user2@example.com"},
    "user3": {"password": "user3pass", "token": "p9o8i7u6y5t4r3e2w1q", "email": "user3@example.com"},
    "user4": {"password": "user4pass", "token": "q9w8e7r6t5y4u3i2o1", "email": "user4@example.com"},
}

APIBANK_RUNTIME_NAME = "account_agenda_meeting"
APIBANK_VERIFICATION_CODE = 970420
APIBANK_DATABASE_ENTITY_TYPES = ("account", "agenda", "meeting")


def ensure_apibank_state(state: WorldState) -> None:
    """Seed API-Bank databases that are needed by the selected subset."""
    accounts = state.entities.setdefault("account", {})
    for username, record in APIBANK_ACCOUNT_DATABASE.items():
        accounts.setdefault(username, {"username": username, **dict(record)})
    state.entities.setdefault("agenda", {})
    state.entities.setdefault("meeting", {})
    state.resources.setdefault("api_bank_source", "AlibabaResearch/DAMO-ConvAI api-bank")
    state.policies.setdefault("backend", {})
    state.policies["backend"]["api_bank_runtime"] = APIBANK_RUNTIME_NAME


def persist_apibank_databases(state: WorldState, database_dir: str | Path) -> None:
    """Mirror API-Bank's JSON database dump convention for live-like sessions."""
    path = Path(database_dir)
    path.mkdir(parents=True, exist_ok=True)
    for entity_type, filename in (
        ("account", "Account.json"),
        ("agenda", "Agenda.json"),
        ("meeting", "Meeting.json"),
    ):
        (path / filename).write_text(
            json.dumps(state.entities.get(entity_type, {}), ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )


def call_apibank_api(state: WorldState, api_name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Run one supported API-Bank API and return its official response shape."""
    ensure_apibank_state(state)
    input_parameters = dict(args)
    try:
        output, state_changed = _dispatch_api(state, api_name, args)
    except Exception as exc:
        return {
            "success": False,
            "state_changed": False,
            "observation": _response(api_name, input_parameters, None, str(exc)),
            "error": str(exc),
        }
    return {
        "success": True,
        "state_changed": state_changed,
        "observation": _response(api_name, input_parameters, output, None),
        "error": None,
    }


def _dispatch_api(state: WorldState, api_name: str, args: dict[str, Any]) -> tuple[Any, bool]:
    if api_name == "CheckToken":
        return {"username": _check_token(state, str(args["token"]))}, False
    if api_name == "GetUserToken":
        return {"token": _get_user_token(state, str(args["username"]), str(args["password"]))}, False
    if api_name == "ModifyPassword":
        return _modify_password(state, str(args["token"]), str(args["old_password"]), str(args["new_password"]))
    if api_name == "ForgotPassword":
        return _forgot_password(state, args)
    if api_name == "AddAgenda":
        return _add_agenda(state, args)
    if api_name == "QueryAgenda":
        return _query_agenda(state, args), False
    if api_name == "ModifyAgenda":
        return _modify_agenda(state, args)
    if api_name == "AddMeeting":
        return _add_meeting(state, args)
    if api_name == "QueryMeeting":
        return _query_meeting(state, args), False
    if api_name == "ModifyMeeting":
        return _modify_meeting(state, args)
    raise Exception(f"Unsupported API-Bank API: {api_name}")


def _response(api_name: str, input_parameters: dict[str, Any], output: Any, exception: str | None) -> dict[str, Any]:
    return {
        "api_name": api_name,
        "input": input_parameters,
        "output": output,
        "exception": exception,
    }


def _check_token(state: WorldState, token: str) -> str:
    for username, account in state.entities.get("account", {}).items():
        if account.get("token") == token:
            return str(username)
    raise Exception("The token is invalid.")


def _get_user_token(state: WorldState, username: str, password: str) -> str:
    account = state.get_entity("account", username)
    if account is None:
        raise Exception("The username does not exist.")
    if account.get("password") != password:
        raise Exception("The password is incorrect.")
    return str(account["token"])


def _modify_password(state: WorldState, token: str, old_password: str, new_password: str) -> tuple[dict[str, str], bool]:
    username = _check_token(state, token)
    account = state.get_entity("account", username)
    if account is None:
        raise Exception("The username does not exist.")
    if account.get("password") != old_password:
        raise Exception("The old password is incorrect.")
    updated = dict(account)
    updated["password"] = new_password
    state.set_entity("account", username, updated)
    return {"status": "success"}, True


def _forgot_password(state: WorldState, args: dict[str, Any]) -> tuple[int | str, bool]:
    status = args.get("status")
    if status == "Forgot Password":
        if "username" not in args or "email" not in args:
            raise Exception("The username and email are required for the first call.")
        username = str(args["username"])
        email = str(args["email"])
        account = state.get_entity("account", username)
        if account is None:
            raise Exception("The username does not exist.")
        if account.get("email") != email:
            raise Exception("The email is incorrect.")
        state.set_entity("password_reset", "current", {
            "username": username,
            "verification_code": APIBANK_VERIFICATION_CODE,
            "status": "issued",
            "consumed": False,
            "issued_at": state.now(),
        })
        return APIBANK_VERIFICATION_CODE, True

    if status == "Verification Code":
        reset = state.get_entity("password_reset", "current")
        if not reset or reset.get("consumed"):
            raise Exception("You need to call the API with status 'Forgot Password' at first.")
        if "new_password" not in args or "verification_code" not in args:
            raise Exception("The new password and verification code are required for the second call.")
        if str(reset.get("verification_code")) != str(args["verification_code"]):
            raise Exception("The verification code is incorrect.")
        username = str(reset["username"])
        account = state.get_entity("account", username)
        if account is None:
            raise Exception("The username does not exist.")
        updated_account = dict(account)
        updated_account["password"] = args["new_password"]
        state.set_entity("account", username, updated_account)
        updated_reset = dict(reset)
        updated_reset["status"] = "consumed"
        updated_reset["consumed"] = True
        updated_reset["consumed_at"] = state.now()
        state.set_entity("password_reset", "current", updated_reset)
        return "success", True

    raise Exception("The status is only 'Forgot Password' or 'Verification Code'.")


def _add_agenda(state: WorldState, args: dict[str, Any]) -> tuple[str, bool]:
    _parse_time(str(args["time"]), required=True)
    content = str(args["content"])
    if content.strip() == "":
        raise Exception("Content should not be null")
    username = _check_token(state, str(args["token"]))
    entity_id = str(len(state.entities.get("agenda", {})) + 1)
    state.set_entity("agenda", entity_id, {
        "username": username,
        "content": content,
        "time": str(args["time"]),
        "location": str(args["location"]),
    })
    return "success", True


def _query_agenda(state: WorldState, args: dict[str, Any]) -> dict[str, Any]:
    time = str(args.get("time", ""))
    content = str(args.get("content", ""))
    if time:
        _parse_time(time, required=False)
    username = _check_token(state, str(args["token"]))
    for agenda in state.entities.get("agenda", {}).values():
        if agenda.get("username") == username and (agenda.get("content") == content or agenda.get("time") == time):
            return dict(agenda)
    if content:
        raise Exception(f"You have no agenda about {content}")
    if time:
        raise Exception(f"You have no agenda at time : {time}")
    raise Exception("Error")


def _modify_agenda(state: WorldState, args: dict[str, Any]) -> tuple[str, bool]:
    time = str(args.get("time", ""))
    content = str(args.get("content", ""))
    if time:
        _parse_time(time, required=False)
    username = _check_token(state, str(args["token"]))
    for entity_id, agenda in state.entities.get("agenda", {}).items():
        if agenda.get("username") == username and (agenda.get("content") == content or agenda.get("time") == time):
            state.set_entity("agenda", str(entity_id), {
                "username": username,
                "content": content,
                "time": time,
                "location": str(args["location"]),
            })
            return "success", True
    if content:
        raise Exception(f"You have no agenda about {content}")
    if time:
        raise Exception(f"You have no agenda at time : {time}")
    raise Exception("Error")


def _add_meeting(state: WorldState, args: dict[str, Any]) -> tuple[str, bool]:
    _parse_time(str(args["start_time"]), required=True)
    _parse_time(str(args["end_time"]), required=True)
    topic = str(args["meeting_topic"])
    if topic.strip() == "":
        raise Exception("Meeting Topic should not be null")
    username = _check_token(state, str(args["token"]))
    existing_ids = [int(entity_id) for entity_id in state.entities.get("meeting", {}) if str(entity_id).isdigit()]
    entity_id = str(max(existing_ids) + 1) if existing_ids else "0"
    state.set_entity("meeting", entity_id, {
        "username": username,
        "meeting_topic": topic,
        "start_time": str(args["start_time"]),
        "end_time": str(args["end_time"]),
        "location": str(args["location"]),
        "attendees": list(args["attendees"]),
    })
    return "success", True


def _query_meeting(state: WorldState, args: dict[str, Any]) -> dict[str, Any]:
    start_time = str(args.get("start_time", ""))
    end_time = str(args.get("end_time", ""))
    topic = str(args.get("meeting_topic", ""))
    if start_time:
        _parse_time(start_time, required=False)
    if end_time:
        _parse_time(end_time, required=False)
    if topic.strip() == "" and not start_time:
        raise Exception("Meeting Topic and start_time should not be null both")
    username = _check_token(state, str(args["token"]))
    for meeting in state.entities.get("meeting", {}).values():
        if meeting.get("username") == username and (meeting.get("meeting_topic") == topic or meeting.get("start_time") == start_time):
            return dict(meeting)
    if topic:
        raise Exception(f"You have no meeting about {topic}")
    if start_time:
        raise Exception(f"You have no meeting at time : {start_time}")
    raise Exception("Error")


def _modify_meeting(state: WorldState, args: dict[str, Any]) -> tuple[str, bool]:
    start_time = str(args.get("start_time", ""))
    end_time = str(args.get("end_time", ""))
    topic = str(args.get("meeting_topic", ""))
    if start_time:
        _parse_time(start_time, required=False)
    if end_time:
        _parse_time(end_time, required=False)
    if topic.strip() == "" and not start_time:
        raise Exception("Meeting Topic and start_time should not be null both")
    username = _check_token(state, str(args["token"]))
    for entity_id, meeting in state.entities.get("meeting", {}).items():
        if meeting.get("username") == username and (meeting.get("meeting_topic") == topic or meeting.get("start_time") == start_time):
            updated = dict(meeting)
            if topic:
                updated["meeting_topic"] = topic
            if start_time:
                updated["start_time"] = start_time
                updated["end_time"] = end_time
            state.set_entity("meeting", str(entity_id), updated)
            return "success", True
    if topic:
        raise Exception(f"You have no meeting about {topic}")
    if start_time:
        raise Exception(f"You have no meeting at time : {start_time}")
    raise Exception("Error")


def _parse_time(value: str, *, required: bool) -> None:
    if not value and not required:
        return
    datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
