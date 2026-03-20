"""
experiment_runner.py — 最小可运行的 experiment runner 原型

负责：
  - 初始化 WorldState
  - 顺序执行预定义 tool calls
  - 自动记录 trace
  - 自动运行 call-level / state-level evaluator
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from toolsim.evaluator import CallEvaluationResult, CallLevelEvaluator, StateEvaluationResult, StateLevelEvaluator
from toolsim.stateful_executor import ExecutionRecord, StatefulExecutor, create_default_tool_registry
from toolsim.stateful_tracer import TraceRecorder
from toolsim.world_state import WorldState


@dataclass
class ExperimentResult:
    final_state: WorldState
    trace: List[ExecutionRecord]
    call_metrics: CallEvaluationResult
    state_metrics: Optional[StateEvaluationResult]
    all_calls_succeeded: bool
    final_state_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "final_state": self.final_state.to_dict(),
            "trace": [record.to_dict() for record in self.trace],
            "call_metrics": self.call_metrics.to_dict(),
            "state_metrics": self.state_metrics.to_dict() if self.state_metrics is not None else None,
            "all_calls_succeeded": self.all_calls_succeeded,
            "final_state_hash": self.final_state_hash,
        }


class ExperimentRunner:
    """执行一组预定义 tool calls，并汇总最小实验结果。"""

    def __init__(
        self,
        executor: Optional[StatefulExecutor] = None,
        call_evaluator: Optional[CallLevelEvaluator] = None,
        state_evaluator: Optional[StateLevelEvaluator] = None,
    ) -> None:
        self._executor = executor
        self._call_evaluator = call_evaluator or CallLevelEvaluator()
        self._state_evaluator = state_evaluator or StateLevelEvaluator()

    def run(
        self,
        tool_calls: List[Dict[str, Any]],
        initial_state: Optional[WorldState] = None,
        goals: Optional[List[Dict[str, Any]]] = None,
    ) -> ExperimentResult:
        state = initial_state if initial_state is not None else WorldState()
        tracer = TraceRecorder()
        executor = self._build_executor(tracer)

        for tool_call in tool_calls:
            tool_name = tool_call.get("tool_name", "")
            args = tool_call.get("args", {})
            executor.execute(tool_name, state, args)

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

    def _build_executor(self, tracer: TraceRecorder) -> StatefulExecutor:
        if self._executor is not None:
            return StatefulExecutor(self._executor._tools, tracer=tracer)
        return StatefulExecutor(create_default_tool_registry(), tracer=tracer)


def build_file_search_demo_calls() -> List[Dict[str, Any]]:
    """构造最小 file/search 演示实验调用序列。"""
    return [
        {"tool_name": "file.write", "args": {"file_id": "f1", "content": "hello world"}},
        {"tool_name": "search.query", "args": {"query": "hello"}},
        {"tool_name": "search.index", "args": {"file_id": "f1"}},
        {"tool_name": "search.query", "args": {"query": "hello"}},
    ]


def build_file_search_demo_goals() -> List[Dict[str, Any]]:
    """构造与最小 file/search 演示匹配的 goals。"""
    return [
        {"type": "entity_exists", "entity_type": "file", "entity_id": "f1"},
        {"type": "indexed_contains", "file_id": "f1", "substring": "hello"},
        {"type": "query_hits_file", "query": "hello", "file_id": "f1"},
    ]
