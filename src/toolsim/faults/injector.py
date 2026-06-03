"""Structured fault injection for stateful tool execution.

The injector is intentionally deterministic by default so benchmark cases stay
reproducible. A profile can opt specific tools into latency, transient failures,
timeouts, schema drift, stale observations, and vague observations.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any

from toolsim.core.tool_spec import ToolExecutionResult


@dataclass
class FaultDecision:
    """Decision returned by a fault injector before or after a tool call."""

    fail_before_execution: bool = False
    error: str | None = None
    latency_ms: float = 0.0
    fault_type: str | None = None


@dataclass
class FaultProfile:
    """Declarative, deterministic fault configuration.

    Attributes:
        latency_ms_by_tool: Tool-name to artificial latency in milliseconds.
        transient_failures: Tool-name to number of calls that should fail before
            normal execution resumes.
        timeout_failures: Tool-name to number of calls that should fail before
            execution with a timeout-like observation.
        schema_drift_failures: Tool-name to number of calls that should fail
            before execution as if the tool schema no longer matched the call.
        stale_observation_tools: Tool names whose observations should replay the
            previous observation for the same tool once one exists.
        vague_error_tools: Tool names whose failed observations should hide the
            underlying error message.
        vague_observation_tools: Tool names whose successful observations should
            be replaced by a low-information observation.
    """

    latency_ms_by_tool: dict[str, float] = field(default_factory=dict)
    transient_failures: dict[str, int] = field(default_factory=dict)
    timeout_failures: dict[str, int] = field(default_factory=dict)
    schema_drift_failures: dict[str, int] = field(default_factory=dict)
    stale_observation_replays: dict[str, int] = field(default_factory=dict)
    stale_observation_tools: set[str] = field(default_factory=set)
    vague_error_tools: set[str] = field(default_factory=set)
    vague_observation_tools: set[str] = field(default_factory=set)
    vague_observation_failures: dict[str, int] = field(default_factory=dict)
    misleading_observations_by_tool: dict[str, dict[str, Any]] = field(default_factory=dict)
    misleading_observation_failures: dict[str, int] = field(default_factory=dict)
    vague_error_message: str = "Tool failed due to a temporary environment issue."
    vague_observation_message: str = "Observation is unavailable or too vague to determine the exact result."

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FaultProfile":
        return cls(
            latency_ms_by_tool={str(k): float(v) for k, v in data.get("latency_ms_by_tool", {}).items()},
            transient_failures={str(k): int(v) for k, v in data.get("transient_failures", {}).items()},
            timeout_failures={str(k): int(v) for k, v in data.get("timeout_failures", {}).items()},
            schema_drift_failures={str(k): int(v) for k, v in data.get("schema_drift_failures", {}).items()},
            stale_observation_replays={str(k): int(v) for k, v in data.get("stale_observation_replays", {}).items()},
            stale_observation_tools=set(data.get("stale_observation_tools", [])),
            vague_error_tools=set(data.get("vague_error_tools", [])),
            vague_observation_tools=set(data.get("vague_observation_tools", [])),
            vague_observation_failures={str(k): int(v) for k, v in data.get("vague_observation_failures", {}).items()},
            misleading_observations_by_tool={
                str(k): dict(v) for k, v in data.get("misleading_observations_by_tool", {}).items()
            },
            misleading_observation_failures={
                str(k): int(v) for k, v in data.get("misleading_observation_failures", {}).items()
            },
            vague_error_message=str(data.get("vague_error_message", cls.vague_error_message)),
            vague_observation_message=str(data.get("vague_observation_message", cls.vague_observation_message)),
        )


class FaultInjector:
    """Apply deterministic faults around tool execution."""

    def __init__(self, profile: FaultProfile | None = None) -> None:
        self.profile = profile or FaultProfile()
        self._remaining_transient_failures = dict(self.profile.transient_failures)
        self._remaining_timeout_failures = dict(self.profile.timeout_failures)
        self._remaining_schema_drift_failures = dict(self.profile.schema_drift_failures)
        self._remaining_stale_observation_replays = dict(self.profile.stale_observation_replays)
        self._remaining_vague_observation_failures = dict(self.profile.vague_observation_failures)
        self._remaining_misleading_observation_failures = dict(self.profile.misleading_observation_failures)
        self._last_observation_by_tool: dict[str, dict[str, Any]] = {}

    def before_call(self, tool_name: str, args: dict[str, Any] | None = None) -> FaultDecision:
        remaining_timeout = self._remaining_timeout_failures.get(tool_name, 0)
        if remaining_timeout > 0:
            self._remaining_timeout_failures[tool_name] = remaining_timeout - 1
            return FaultDecision(
                fail_before_execution=True,
                error=f"Timeout injected for {tool_name}",
                latency_ms=self.profile.latency_ms_by_tool.get(tool_name, 0.0),
                fault_type="timeout",
            )

        remaining_schema_drift = self._remaining_schema_drift_failures.get(tool_name, 0)
        if remaining_schema_drift > 0:
            self._remaining_schema_drift_failures[tool_name] = remaining_schema_drift - 1
            arg_keys = ", ".join(sorted((args or {}).keys())) or "no arguments"
            return FaultDecision(
                fail_before_execution=True,
                error=f"Schema drift injected for {tool_name}; received arguments: {arg_keys}",
                latency_ms=self.profile.latency_ms_by_tool.get(tool_name, 0.0),
                fault_type="schema_drift",
            )

        remaining = self._remaining_transient_failures.get(tool_name, 0)
        if remaining > 0:
            self._remaining_transient_failures[tool_name] = remaining - 1
            return FaultDecision(
                fail_before_execution=True,
                error=f"Transient failure injected for {tool_name}",
                latency_ms=self.profile.latency_ms_by_tool.get(tool_name, 0.0),
                fault_type="transient_failure",
            )
        return FaultDecision(latency_ms=self.profile.latency_ms_by_tool.get(tool_name, 0.0))

    def after_call(self, tool_name: str, result: ToolExecutionResult) -> ToolExecutionResult:
        adjusted = copy.deepcopy(result)

        if self._should_apply_stale(tool_name):
            previous = self._last_observation_by_tool.get(tool_name)
            if previous is not None:
                if tool_name in self._remaining_stale_observation_replays:
                    self._remaining_stale_observation_replays[tool_name] -= 1
                adjusted.observation = copy.deepcopy(previous)
                adjusted.metadata = {
                    **adjusted.metadata,
                    "fault": "stale_observation",
                    "stale_observation_replayed": True,
                }
            self._last_observation_by_tool[tool_name] = copy.deepcopy(result.observation)

        if not adjusted.success and tool_name in self.profile.vague_error_tools:
            adjusted.metadata = {
                **adjusted.metadata,
                "fault": "vague_error",
                "original_error": adjusted.error,
            }
            adjusted.error = self.profile.vague_error_message
            adjusted.observation = {"error": self.profile.vague_error_message}

        if adjusted.success and self._should_apply_misleading_observation(tool_name):
            if tool_name in self._remaining_misleading_observation_failures:
                self._remaining_misleading_observation_failures[tool_name] -= 1
            adjusted.metadata = {
                **adjusted.metadata,
                "fault": "misleading_observation",
                "original_observation": adjusted.observation,
            }
            adjusted.observation = copy.deepcopy(self.profile.misleading_observations_by_tool[tool_name])

        if adjusted.success and self._should_apply_vague_observation(tool_name):
            if tool_name in self._remaining_vague_observation_failures:
                self._remaining_vague_observation_failures[tool_name] -= 1
            adjusted.metadata = {
                **adjusted.metadata,
                "fault": "vague_observation",
                "original_observation": adjusted.observation,
            }
            adjusted.observation = {"message": self.profile.vague_observation_message}

        return adjusted

    def _should_apply_stale(self, tool_name: str) -> bool:
        if tool_name in self._remaining_stale_observation_replays:
            return self._remaining_stale_observation_replays[tool_name] > 0
        return tool_name in self.profile.stale_observation_tools

    def _should_apply_vague_observation(self, tool_name: str) -> bool:
        if tool_name in self._remaining_vague_observation_failures:
            return self._remaining_vague_observation_failures[tool_name] > 0
        return tool_name in self.profile.vague_observation_tools

    def _should_apply_misleading_observation(self, tool_name: str) -> bool:
        if tool_name not in self.profile.misleading_observations_by_tool:
            return False
        if tool_name in self._remaining_misleading_observation_failures:
            return self._remaining_misleading_observation_failures[tool_name] > 0
        return True
