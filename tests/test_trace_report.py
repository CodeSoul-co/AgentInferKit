"""Unit tests for stateful trace Markdown reports."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toolsim.reporting.trace_report import render_stateful_trace_markdown, write_stateful_trace_markdown
from toolsim.runners.experiment_runner import ExperimentRunner


def test_trace_report_contains_core_execution_signals():
    result = ExperimentRunner().run(
        tool_calls=[
            {"tool_name": "issue.create", "args": {"issue_id": "iss1", "title": "Bug"}},
            {"tool_name": "issue.assign", "args": {"issue_id": "iss1", "assignee": "bob"}},
        ],
        permissions={"issue.create", "issue.assign"},
    )

    report = render_stateful_trace_markdown(result)

    assert "# Stateful Tool Trace Report" in report
    assert "`issue.create`" in report
    assert "`issue.assign`" in report
    assert "State hash" in report
    assert "State diff:" in report
    assert "Created `issue.iss1`" in report
    assert "Updated `issue.iss1`" in report
    assert "`assignee`: None -> 'bob'" in report
    assert "Final World State" in report
    assert "`issue`: 1" in report


def test_trace_report_can_be_written_to_disk(tmp_path):
    result = ExperimentRunner().run(
        tool_calls=[
            {"tool_name": "file.write", "args": {"file_id": "f1", "content": "hello"}},
        ],
        permissions={"file.write"},
    )

    path = write_stateful_trace_markdown(result, tmp_path / "trace.md")

    assert path.exists()
    assert "file.write" in path.read_text(encoding="utf-8")
