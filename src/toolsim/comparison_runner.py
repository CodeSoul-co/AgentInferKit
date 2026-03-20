"""
comparison_runner.py — 最小可运行的 Stateless vs Stateful 对比执行器
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from toolsim.experiment_runner import ExperimentRunner, ExperimentResult
from toolsim.stateless_baseline import StatelessExperimentRunner
from toolsim.world_state import WorldState


@dataclass
class ComparisonCase:
    case_name: str
    description: str
    stateful_tool_calls: List[Dict[str, Any]]
    stateless_tool_calls: List[Dict[str, Any]]
    goals_stateful: Optional[List[Dict[str, Any]]] = None
    goals_stateless: Optional[List[Dict[str, Any]]] = None


@dataclass
class ComparisonResult:
    case_name: str
    stateful_result: ExperimentResult
    stateless_result: ExperimentResult
    summary: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_name": self.case_name,
            "stateful_result": self.stateful_result.to_dict(),
            "stateless_result": self.stateless_result.to_dict(),
            "summary": self.summary,
        }

    def to_readable_summary(self) -> Dict[str, Any]:
        """导出一个更适合直接查看的紧凑摘要。"""
        return {
            "case_name": self.case_name,
            "stateful_trace_length": len(self.stateful_result.trace),
            "stateless_trace_length": len(self.stateless_result.trace),
            "stateful_final_hits": _extract_last_query_hits(self.stateful_result),
            "stateless_final_hits": _extract_last_query_hits(self.stateless_result),
            "stateful_call_metrics": self.stateful_result.call_metrics.to_dict(),
            "stateless_call_metrics": self.stateless_result.call_metrics.to_dict(),
            "stateful_state_metrics": (
                self.stateful_result.state_metrics.to_dict()
                if self.stateful_result.state_metrics is not None
                else None
            ),
            "stateless_state_metrics": (
                self.stateless_result.state_metrics.to_dict()
                if self.stateless_result.state_metrics is not None
                else None
            ),
            "summary": self.summary,
        }


class ComparisonRunner:
    """运行单个对比 case 的 stateful / stateless 实验。"""

    def __init__(
        self,
        stateful_runner: Optional[ExperimentRunner] = None,
        stateless_runner: Optional[StatelessExperimentRunner] = None,
    ) -> None:
        self._stateful_runner = stateful_runner or ExperimentRunner()
        self._stateless_runner = stateless_runner or StatelessExperimentRunner()

    def run_case(self, case: ComparisonCase) -> ComparisonResult:
        stateful_result = self._stateful_runner.run(
            tool_calls=case.stateful_tool_calls,
            initial_state=WorldState(),
            goals=case.goals_stateful,
        )
        stateless_result = self._stateless_runner.run(
            tool_calls=case.stateless_tool_calls,
            initial_state=WorldState(),
            goals=case.goals_stateless,
        )

        summary = {
            "stateful_all_calls_succeeded": stateful_result.all_calls_succeeded,
            "stateless_all_calls_succeeded": stateless_result.all_calls_succeeded,
            "stateful_all_goals_passed": (
                stateful_result.state_metrics.all_passed if stateful_result.state_metrics is not None else None
            ),
            "stateless_all_goals_passed": (
                stateless_result.state_metrics.all_passed if stateless_result.state_metrics is not None else None
            ),
        }

        return ComparisonResult(
            case_name=case.case_name,
            stateful_result=stateful_result,
            stateless_result=stateless_result,
            summary=summary,
        )

    def run_cases(self, cases: List[ComparisonCase]) -> List[ComparisonResult]:
        """顺序运行多个 comparison cases。"""
        return [self.run_case(case) for case in cases]

    def run_cases_with_readable_summary(self, cases: List[ComparisonCase]) -> List[Dict[str, Any]]:
        """顺序运行多个 comparison cases，并返回便于查看的摘要列表。"""
        return [result.to_readable_summary() for result in self.run_cases(cases)]


def build_stateless_vs_stateful_cases() -> List[ComparisonCase]:
    """构造突出显式索引依赖差异的最小案例集合。"""
    return [
        ComparisonCase(
            case_name="write_then_query",
            description="Stateful requires explicit indexing before search can hit; stateless searches current file content directly.",
            stateful_tool_calls=[
                {"tool_name": "file.write", "args": {"file_id": "f1", "content": "hello world"}},
                {"tool_name": "search.query", "args": {"query": "hello"}},
            ],
            stateless_tool_calls=[
                {"tool_name": "file.write", "args": {"file_id": "f1", "content": "hello world"}},
                {"tool_name": "search.query", "args": {"query": "hello"}},
            ],
            goals_stateful=[
                {"type": "entity_exists", "entity_type": "file", "entity_id": "f1"},
            ],
            goals_stateless=[
                {"type": "entity_exists", "entity_type": "file", "entity_id": "f1"},
                {"type": "query_hits_file", "query": "hello", "file_id": "f1"},
            ],
        ),
        ComparisonCase(
            case_name="write_index_query",
            description="Both settings can hit the file, but stateful needs an explicit search.index step.",
            stateful_tool_calls=[
                {"tool_name": "file.write", "args": {"file_id": "f1", "content": "hello world"}},
                {"tool_name": "search.index", "args": {"file_id": "f1"}},
                {"tool_name": "search.query", "args": {"query": "hello"}},
            ],
            stateless_tool_calls=[
                {"tool_name": "file.write", "args": {"file_id": "f1", "content": "hello world"}},
                {"tool_name": "search.query", "args": {"query": "hello"}},
            ],
            goals_stateful=[
                {"type": "entity_exists", "entity_type": "file", "entity_id": "f1"},
                {"type": "indexed_contains", "file_id": "f1", "substring": "hello"},
                {"type": "query_hits_file", "query": "hello", "file_id": "f1"},
            ],
            goals_stateless=[
                {"type": "entity_exists", "entity_type": "file", "entity_id": "f1"},
                {"type": "query_hits_file", "query": "hello", "file_id": "f1"},
            ],
        ),
        ComparisonCase(
            case_name="overwrite_without_reindex",
            description="Stateful search can stay on the stale indexed snapshot, while stateless search reflects the latest file content.",
            stateful_tool_calls=[
                {"tool_name": "file.write", "args": {"file_id": "f1", "content": "old hello"}},
                {"tool_name": "search.index", "args": {"file_id": "f1"}},
                {"tool_name": "file.write", "args": {"file_id": "f1", "content": "new gamma"}},
                {"tool_name": "search.query", "args": {"query": "hello"}},
            ],
            stateless_tool_calls=[
                {"tool_name": "file.write", "args": {"file_id": "f1", "content": "old hello"}},
                {"tool_name": "file.write", "args": {"file_id": "f1", "content": "new gamma"}},
                {"tool_name": "search.query", "args": {"query": "hello"}},
            ],
            goals_stateful=[
                {"type": "query_hits_file", "query": "hello", "file_id": "f1"},
            ],
            goals_stateless=[
                {"type": "entity_field_equals", "entity_type": "file", "entity_id": "f1", "field": "content", "expected": "new gamma"},
            ],
        ),
    ]


def _extract_last_query_hits(result: ExperimentResult) -> List[Dict[str, Any]]:
    for record in reversed(result.trace):
        if record.tool_name == "search.query":
            return record.observation.get("hits", [])
    return []
