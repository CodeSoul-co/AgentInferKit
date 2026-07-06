"""API-Bank-derived tools for live-like backend migration experiments."""

from __future__ import annotations

from typing import Any

from toolsim.core.tool_spec import ExecutionContext, ToolExecutionResult, ToolMetadata, ToolSpec
from toolsim.tools.apibank_runtime import call_apibank_api


def _schema(properties: dict[str, dict[str, str]], required: list[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }


def _execute_api_tool(state_or_context: Any, args: dict[str, Any], api_name: str) -> ToolExecutionResult:
    state = state_or_context.state if isinstance(state_or_context, ExecutionContext) else state_or_context
    backend = getattr(state_or_context, "backend", None)

    if backend is not None and hasattr(backend, "call_apibank_api"):
        api_result = backend.call_apibank_api(state, api_name, args)
    else:
        api_result = call_apibank_api(state, api_name, args)

    observation = dict(api_result["observation"])
    if not api_result["success"]:
        return ToolExecutionResult(
            success=False,
            error=api_result["error"],
            observation=observation,
            state_changed=bool(api_result["state_changed"]),
            metadata={"api_bank": True},
        )
    return ToolExecutionResult(
        success=True,
        observation=observation,
        state_changed=bool(api_result["state_changed"]),
        metadata={"api_bank": True},
    )


class APIBankToolBase(ToolSpec):
    tool_name = ""
    description = ""
    input_schema: dict[str, Any] = {}
    idempotency = "unknown"

    def execute(self, state_or_context: Any, args: dict[str, Any]) -> ToolExecutionResult:
        return _execute_api_tool(state_or_context, args, self.tool_name)

    @classmethod
    def _metadata(cls) -> ToolMetadata:
        return ToolMetadata(
            name=cls.tool_name,
            version="0.2",
            domain="api_bank",
            description=cls.description,
            input_schema=cls.input_schema,
            idempotency=cls.idempotency,
        )


class CheckTokenTool(APIBankToolBase):
    tool_name = "CheckToken"
    description = "Check a user token and return the username."
    input_schema = _schema({"token": {"type": "string"}}, ["token"])
    idempotency = "idempotent"


CheckTokenTool.metadata = CheckTokenTool._metadata()


class GetUserTokenTool(APIBankToolBase):
    tool_name = "GetUserToken"
    description = "Get the user token by username and password."
    input_schema = _schema(
        {
            "username": {"type": "string"},
            "password": {"type": "string"},
        },
        ["username", "password"],
    )
    idempotency = "idempotent"


GetUserTokenTool.metadata = GetUserTokenTool._metadata()


class ModifyPasswordTool(APIBankToolBase):
    tool_name = "ModifyPassword"
    description = "Modify the password of an account after token verification."
    input_schema = _schema(
        {
            "token": {"type": "string"},
            "old_password": {"type": "string"},
            "new_password": {"type": "string"},
        },
        ["token", "old_password", "new_password"],
    )
    idempotency = "non_idempotent"


ModifyPasswordTool.metadata = ModifyPasswordTool._metadata()


class ForgotPasswordTool(APIBankToolBase):
    tool_name = "ForgotPassword"
    description = (
        "Send an email reset code, then verify the code to change the account password."
    )
    input_schema = _schema(
        {
            "status": {"type": "string"},
            "username": {"type": "string"},
            "email": {"type": "string"},
            "verification_code": {"type": "integer"},
            "new_password": {"type": "string"},
        },
        ["status"],
    )
    idempotency = "non_idempotent"


ForgotPasswordTool.metadata = ForgotPasswordTool._metadata()


class AddAgendaTool(APIBankToolBase):
    tool_name = "AddAgenda"
    description = "Add an agenda item with content, time, and location."
    input_schema = _schema(
        {
            "token": {"type": "string"},
            "content": {"type": "string"},
            "time": {"type": "string"},
            "location": {"type": "string"},
        },
        ["token", "content", "time", "location"],
    )
    idempotency = "non_idempotent"


AddAgendaTool.metadata = AddAgendaTool._metadata()


class QueryAgendaTool(APIBankToolBase):
    tool_name = "QueryAgenda"
    description = "Query a user's agenda item by content or time."
    input_schema = AddAgendaTool.input_schema
    idempotency = "idempotent"


QueryAgendaTool.metadata = QueryAgendaTool._metadata()


class ModifyAgendaTool(APIBankToolBase):
    tool_name = "ModifyAgenda"
    description = "Modify an agenda item by matching its content or time."
    input_schema = AddAgendaTool.input_schema
    idempotency = "non_idempotent"


ModifyAgendaTool.metadata = ModifyAgendaTool._metadata()


_MEETING_SCHEMA = _schema(
    {
        "token": {"type": "string"},
        "meeting_topic": {"type": "string"},
        "start_time": {"type": "string"},
        "end_time": {"type": "string"},
        "location": {"type": "string"},
        "attendees": {"type": "array"},
    },
    ["token", "meeting_topic", "start_time", "end_time", "location", "attendees"],
)


class AddMeetingTool(APIBankToolBase):
    tool_name = "AddMeeting"
    description = "Reserve a meeting and store topic, time, location, and attendees."
    input_schema = _MEETING_SCHEMA
    idempotency = "non_idempotent"


AddMeetingTool.metadata = AddMeetingTool._metadata()


class QueryMeetingTool(APIBankToolBase):
    tool_name = "QueryMeeting"
    description = "Query a user's meeting by topic or start time."
    input_schema = _MEETING_SCHEMA
    idempotency = "idempotent"


QueryMeetingTool.metadata = QueryMeetingTool._metadata()


class ModifyMeetingTool(APIBankToolBase):
    tool_name = "ModifyMeeting"
    description = "Modify a meeting reservation by matching topic or start time."
    input_schema = _MEETING_SCHEMA
    idempotency = "non_idempotent"


ModifyMeetingTool.metadata = ModifyMeetingTool._metadata()


APIBANK_TOOLS: dict[str, ToolSpec] = {
    tool.tool_name: tool()
    for tool in (
        CheckTokenTool,
        GetUserTokenTool,
        ModifyPasswordTool,
        ForgotPasswordTool,
        AddAgendaTool,
        QueryAgendaTool,
        ModifyAgendaTool,
        AddMeetingTool,
        QueryMeetingTool,
        ModifyMeetingTool,
    )
}
