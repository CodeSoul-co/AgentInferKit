"""Focused tests for custom_agent tool runtime switching."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fastapi.testclient import TestClient
from main import app
from api import custom_agent as custom_agent_module


client = TestClient(app)


def _write_dataset(tmp_path: Path) -> Path:
    dataset_path = tmp_path / "agent_dataset.jsonl"
    dataset_path.write_text(
        '{"sample_id": "s1", "question": "Fix issue", "task_type": "api_calling", "answer": "done"}\n',
        encoding="utf-8",
    )
    return dataset_path


def test_custom_agent_stateful_runtime_tool_call(tmp_path):
    dataset_path = _write_dataset(tmp_path)
    create_resp = client.post(
        "/api/v1/agent/sessions",
        json={
            "agent_name": "tester",
            "dataset_path": str(dataset_path),
            "tool_runtime": "stateful",
            "tool_backend": "mock",
            "tool_permissions": ["issue.create", "issue.assign"],
        },
    )
    assert create_resp.status_code == 200
    session_id = create_resp.json()["data"]["session_id"]

    first = client.post(
        f"/api/v1/agent/sessions/{session_id}/tool_call",
        json={"sample_id": "s1", "tool_id": "issue.create", "parameters": {"issue_id": "iss1", "title": "Bug"}},
    )
    second = client.post(
        f"/api/v1/agent/sessions/{session_id}/tool_call",
        json={"sample_id": "s1", "tool_id": "issue.assign", "parameters": {"issue_id": "iss1", "assignee": "bob"}},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["data"]["success"] is True
    assert second.json()["data"]["success"] is True
    assert second.json()["data"]["observation"]["state_changed"] is True


def test_custom_agent_legacy_runtime_remains_default(tmp_path):
    dataset_path = _write_dataset(tmp_path)
    create_resp = client.post(
        "/api/v1/agent/sessions",
        json={
            "agent_name": "tester",
            "dataset_path": str(dataset_path),
        },
    )
    assert create_resp.status_code == 200
    session_id = create_resp.json()["data"]["session_id"]

    tool_resp = client.post(
        f"/api/v1/agent/sessions/{session_id}/tool_call",
        json={"sample_id": "s1", "tool_id": "missing.tool", "parameters": {}},
    )

    assert tool_resp.status_code == 200
    assert tool_resp.json()["data"]["success"] is True
    assert "tool_id" in tool_resp.json()["data"]["observation"]


def teardown_function(_func):
    for session_id in list(custom_agent_module._sessions.keys()):
        custom_agent_module._stateful_runtime.reset_session(session_id)
    custom_agent_module._sessions.clear()
