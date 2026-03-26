"""Experiment runner: execute predefined tool-call sequences and evaluate outcomes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from toolsim.backends.base import BaseBackend
from toolsim.backends.mock_backend import MockBackend
from toolsim.core.environment import ToolEnvironment
from toolsim.core.world_state import WorldState
from toolsim.evaluators.evaluator import (
    CallEvaluationResult,
    CallLevelEvaluator,
    StateEvaluationResult,
    StateLevelEvaluator,
)
from toolsim.execution.stateful_executor import (
    ExecutionRecord,
    ExecutorConfig,
    StatefulExecutor,
    create_default_tool_registry,
)
from toolsim.execution.stateful_tracer import TraceRecorder


@dataclass
class ExperimentResult:
    """Result of a single experiment run."""

    final_state: WorldState
    trace: list[ExecutionRecord]
    call_metrics: CallEvaluationResult
    state_metrics: StateEvaluationResult | None
    all_calls_succeeded: bool
    final_state_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "final_state": self.final_state.to_dict(),
            "trace": [record.to_dict() for record in self.trace],
            "call_metrics": self.call_metrics.to_dict(),
            "state_metrics": self.state_metrics.to_dict() if self.state_metrics is not None else None,
            "all_calls_succeeded": self.all_calls_succeeded,
            "final_state_hash": self.final_state_hash,
        }


class ExperimentRunner:
    """Execute a sequence of predefined tool calls and evaluate the outcome."""

    def __init__(
        self,
        executor: StatefulExecutor | None = None,
        call_evaluator: CallLevelEvaluator | None = None,
        state_evaluator: StateLevelEvaluator | None = None,
        executor_config: ExecutorConfig | None = None,
        backend: BaseBackend | None = None,
    ) -> None:
        self._executor = executor
        self._call_evaluator = call_evaluator or CallLevelEvaluator()
        self._state_evaluator = state_evaluator or StateLevelEvaluator()
        self._executor_config = executor_config or ExecutorConfig()
        self._backend = backend or MockBackend()

    def run(
        self,
        tool_calls: list[dict[str, Any]],
        initial_state: WorldState | None = None,
        goals: list[dict[str, Any]] | None = None,
        permissions: set[str] | None = None,
        environment: ToolEnvironment | None = None,
        backend: BaseBackend | None = None,
    ) -> ExperimentResult:
        active_backend = backend or environment.backend if environment is not None else backend or self._backend

        if environment is not None:
            state = environment.state
        elif initial_state is not None:
            state = initial_state
        else:
            state = active_backend.create_state()

        tracer = TraceRecorder()
        executor = self._build_executor(tracer, active_backend)
        env = environment or ToolEnvironment(
            state=state,
            backend=active_backend,
            auto_advance_clock=self._executor_config.auto_advance_clock,
            auto_apply_ready_effects=self._executor_config.auto_apply_ready_effects,
        )

        for tool_call in tool_calls:
            advance_time = tool_call.get("advance_time")
            if advance_time is not None:
                env.advance_time(float(advance_time))

            tool_name = tool_call.get("tool_name", "")
            args = tool_call.get("args", {})
            executor.execute(tool_name, state, args, permissions=permissions, environment=env)

        trace = tracer.get_records()
        call_metrics = self._call_evaluator.evaluate(trace)
        state_metrics = self._state_evaluator.evaluate(state, goals) if goals is not None else None

        return ExperimentResult(
            final_state=state,
            trace=trace,
            call_metrics=call_metrics,
            state_metrics=state_metrics,
            all_calls_succeeded=all(record.success for record in trace),
            final_state_hash=state.compute_hash(),
        )

    def _build_executor(self, tracer: TraceRecorder, backend: BaseBackend) -> StatefulExecutor:
        if self._executor is not None:
            return StatefulExecutor(
                self._executor._tools,
                tracer=tracer,
                config=self._executor_config,
                backend=backend,
            )
        return StatefulExecutor(
            create_default_tool_registry(),
            tracer=tracer,
            config=self._executor_config,
            backend=backend,
        )


def build_file_search_demo_calls() -> list[dict[str, Any]]:
    """Return the default file-search demo tool-call sequence."""
    return [
        {"tool_name": "file.write", "args": {"file_id": "f1", "content": "hello world"}},
        {"tool_name": "search.query", "args": {"query": "hello"}},
        {"tool_name": "search.index", "args": {"file_id": "f1"}},
        {"tool_name": "search.query", "args": {"query": "hello"}},
    ]


def build_file_search_demo_goals() -> list[dict[str, Any]]:
    """Return the default file-search demo goal assertions."""
    return [
        {"type": "entity_exists", "entity_type": "file", "entity_id": "f1"},
        {"type": "indexed_contains", "file_id": "f1", "substring": "hello"},
        {"type": "query_hits_file", "query": "hello", "file_id": "f1"},
    ]


def build_issue_tracker_demo_calls() -> list[dict[str, Any]]:
    """Return the default issue-tracker demo tool-call sequence."""
    return [
        {"tool_name": "issue.create", "args": {"issue_id": "iss1", "title": "Search bug", "reporter": "alice"}},
        {"tool_name": "issue.close", "args": {"issue_id": "iss1", "resolution": "fixed"}},
        {"tool_name": "issue.assign", "args": {"issue_id": "iss1", "assignee": "bob"}},
        {"tool_name": "issue.close", "args": {"issue_id": "iss1", "resolution": "fixed"}},
        {"tool_name": "issue.comment", "args": {"issue_id": "iss1", "comment_id": "c1", "content": "Patched and verified"}},
    ]


def build_issue_tracker_demo_goals() -> list[dict[str, Any]]:
    """Return the default issue-tracker demo goal assertions."""
    return [
        {"type": "issue_exists", "issue_id": "iss1"},
        {"type": "issue_status_is", "issue_id": "iss1", "status": "closed"},
        {"type": "issue_has_assignee", "issue_id": "iss1", "assignee": "bob"},
        {"type": "issue_comment_count_is", "issue_id": "iss1", "count": 1},
    ]
