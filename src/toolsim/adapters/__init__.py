"""Adapters that expose stateful toolsim execution to external callers."""

from toolsim.adapters.stateful_runtime import StatefulToolRuntime, ToolRuntimeResponse
from toolsim.adapters.toolsandbox_adapter import (
    ToolSandboxConvertedCase,
    ToolSandboxScenario,
    build_initial_state,
    convert_toolsandbox_file,
    convert_toolsandbox_scenario,
    load_toolsandbox_scenarios,
    milestones_to_goals,
    milestones_to_oracle_tool_calls,
    write_converted_cases_jsonl,
)

__all__ = [
    "StatefulToolRuntime",
    "ToolRuntimeResponse",
    "ToolSandboxConvertedCase",
    "ToolSandboxScenario",
    "build_initial_state",
    "convert_toolsandbox_file",
    "convert_toolsandbox_scenario",
    "load_toolsandbox_scenarios",
    "milestones_to_goals",
    "milestones_to_oracle_tool_calls",
    "write_converted_cases_jsonl",
]
