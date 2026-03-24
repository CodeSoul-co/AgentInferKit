"""
comparison_runner.py — Stateless vs Stateful comparison runner
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from toolsim.runners.experiment_runner import ExperimentResult, ExperimentRunner
from toolsim.runners.stateless_baseline import StatelessExperimentRunner
from toolsim.core.utils import extract_last_query_hits
from toolsim.core.world_state import WorldState


@dataclass
class ComparisonCase:
    case_name: str
    description: str
    stateful_tool_calls: list[dict[str, Any]]
    stateless_tool_calls: list[dict[str, Any]]
    goals_stateful: list[dict[str, Any]] | None = None
    goals_stateless: list[dict[str, Any]] | None = None


@dataclass
class ComparisonResult:
    case_name: str
    stateful_result: ExperimentResult
    stateless_result: ExperimentResult
    summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_name": self.case_name,
            "stateful_result": self.stateful_result.to_dict(),
            "stateless_result": self.stateless_result.to_dict(),
            "summary": self.summary,
        }

    def to_readable_summary(self) -> dict[str, Any]:
        """Export a compact summary suitable for direct inspection."""
        return {
            "case_name": self.case_name,
            "stateful_trace_length": len(self.stateful_result.trace),
            "stateless_trace_length": len(self.stateless_result.trace),
            "stateful_final_hits": extract_last_query_hits(self.stateful_result.trace),
            "stateless_final_hits": extract_last_query_hits(self.stateless_result.trace),
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
    """Run a single comparison case with both stateful and stateless runners."""

    def __init__(
        self,
        stateful_runner: ExperimentRunner | None = None,
        stateless_runner: StatelessExperimentRunner | None = None,
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

    def run_cases(self, cases: list[ComparisonCase]) -> list[ComparisonResult]:
        """Run multiple comparison cases sequentially."""
        return [self.run_case(case) for case in cases]

    def run_cases_with_readable_summary(self, cases: list[ComparisonCase]) -> list[dict[str, Any]]:
        """Run multiple comparison cases and return a list of human-readable summaries."""
        return [result.to_readable_summary() for result in self.run_cases(cases)]


def build_stateless_vs_stateful_cases() -> list[ComparisonCase]:
    """Build the default case set highlighting explicit-index dependency differences."""
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
