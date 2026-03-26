"""
toolsim — Stateful simulation framework for evaluating LLM tool-use strategies.

Provides a minimal but extensible world model (``WorldState``), a registry
of typed tools (``FileWriteTool``, ``SearchIndexTool``, ``CalendarCreateEventTool``, …),
a stateful executor with pre/postcondition enforcement, side-effect scheduling,
multiple backends, and a multi-level evaluation system (call, state, trajectory).

Quick start::

    from toolsim import WorldState, StatefulExecutor, create_default_tool_registry, TraceRecorder

    state = WorldState()
    tracer = TraceRecorder()
    executor = StatefulExecutor(create_default_tool_registry(), tracer=tracer)

    executor.execute("file.write", state, {"file_id": "f1", "content": "hello"})
    executor.execute("search.index", state, {"file_id": "f1"})
    executor.execute("search.query", state, {"query": "hello"})

    print(tracer.summary())
"""

from __future__ import annotations

# Core state model
from toolsim.core.world_state import (
    PendingEffect,
    PolicyDecision,
    StateSnapshot,
    WorldState,
)

# Tool abstractions
from toolsim.core.tool_spec import (
    ConditionCheckResult,
    ExecutionContext,
    PostconditionSpec,
    PreconditionSpec,
    ToolExecutionResult,
    ToolMetadata,
    ToolSpec,
)

# Environment & effects
from toolsim.core.environment import ToolEnvironment
from toolsim.core.side_effects import (
    EffectApplicationResult,
    SideEffectScheduler,
    create_default_scheduler,
)

# Tool implementations
from toolsim.tools.file_tools import FILE_TOOLS, FileReadTool, FileWriteTool
from toolsim.tools.issue_tools import ISSUE_TOOLS, IssueAssignTool, IssueCloseTool, IssueCommentTool, IssueCreateTool, IssueReopenTool
from toolsim.tools.search_tools import SEARCH_TOOLS, SearchIndexTool, SearchQueryTool
from toolsim.tools.calendar_tools import (
    CALENDAR_TOOLS,
    CalendarCreateEventTool,
    CalendarDeleteEventTool,
    CalendarSearchEventsTool,
    CalendarUpdateEventTool,
)

# Executor & tracing
from toolsim.execution.stateful_executor import (
    ExecutorConfig,
    ExecutionRecord,
    StatefulExecutor,
    create_default_tool_registry,
)
from toolsim.execution.stateful_tracer import TraceRecorder

# Evaluators
from toolsim.evaluators.evaluator import CallLevelEvaluator, StateLevelEvaluator
from toolsim.evaluators.trajectory_evaluator import (
    TrajectoryComparisonSummary,
    TrajectoryLevelEvaluator,
    TrajectoryMetrics,
    detect_explicit_dependency_resolution,
    detect_issue_close_recovery_pattern,
    detect_overwrite_without_reindex_pattern,
    detect_query_before_index,
    summarize_trajectory_difference,
)

# Reporting
from toolsim.reporting.reporting import (
    BatchComparisonResult,
    BatchComparisonRunner,
    CaseComparisonSummary,
    render_markdown_report,
    summarize_comparison_result,
)
from toolsim.evaluators.overview_summary import OverviewMetrics, compute_overview_metrics, generate_overall_conclusion

# Experiment runners
from toolsim.runners.comparison_runner import (
    ComparisonCase,
    ComparisonResult,
    ComparisonRunner,
    build_stateless_vs_stateful_cases,
)
from toolsim.runners.experiment_runner import (
    ExperimentResult,
    ExperimentRunner,
    build_file_search_demo_calls,
    build_file_search_demo_goals,
    build_issue_tracker_demo_calls,
    build_issue_tracker_demo_goals,
)
from toolsim.runners.stateless_baseline import StatelessExperimentRunner

# Registry
from toolsim.core.registry import ToolRegistry

# Backends
from toolsim.backends import BaseBackend, MockBackend, SandboxBackend

# Constants
from toolsim.core.constants import (
    CALENDAR_ALLOWED_STATUSES,
    CALENDAR_DEFAULT_ID,
    EffectStatus,
    EntityType,
    ExecutionStatus,
)

__all__ = [
    # State
    "WorldState",
    "PendingEffect",
    "StateSnapshot",
    "PolicyDecision",
    # Tool spec
    "ToolSpec",
    "ToolMetadata",
    "ToolExecutionResult",
    "ExecutionContext",
    "PreconditionSpec",
    "PostconditionSpec",
    "ConditionCheckResult",
    # Environment
    "ToolEnvironment",
    "SideEffectScheduler",
    "EffectApplicationResult",
    "create_default_scheduler",
    # Tools
    "FILE_TOOLS",
    "SEARCH_TOOLS",
    "CALENDAR_TOOLS",
    "ISSUE_TOOLS",
    "FileWriteTool",
    "FileReadTool",
    "IssueCreateTool",
    "IssueAssignTool",
    "IssueCommentTool",
    "IssueCloseTool",
    "IssueReopenTool",
    "SearchIndexTool",
    "SearchQueryTool",
    "CalendarCreateEventTool",
    "CalendarSearchEventsTool",
    "CalendarUpdateEventTool",
    "CalendarDeleteEventTool",
    # Executor
    "StatefulExecutor",
    "ExecutorConfig",
    "ExecutionRecord",
    "create_default_tool_registry",
    # Tracing
    "TraceRecorder",
    # Evaluators
    "CallLevelEvaluator",
    "StateLevelEvaluator",
    "TrajectoryLevelEvaluator",
    "TrajectoryMetrics",
    "TrajectoryComparisonSummary",
    "detect_query_before_index",
    "detect_explicit_dependency_resolution",
    "detect_overwrite_without_reindex_pattern",
    "detect_issue_close_recovery_pattern",
    "summarize_trajectory_difference",
    # Reporting
    "BatchComparisonRunner",
    "BatchComparisonResult",
    "CaseComparisonSummary",
    "render_markdown_report",
    "summarize_comparison_result",
    "OverviewMetrics",
    "compute_overview_metrics",
    "generate_overall_conclusion",
    # Runners
    "ComparisonRunner",
    "ComparisonCase",
    "ComparisonResult",
    "build_stateless_vs_stateful_cases",
    "ExperimentRunner",
    "ExperimentResult",
    "build_file_search_demo_calls",
    "build_file_search_demo_goals",
    "build_issue_tracker_demo_calls",
    "build_issue_tracker_demo_goals",
    "StatelessExperimentRunner",
    # Registry
    "ToolRegistry",
    # Backends
    "BaseBackend",
    "MockBackend",
    "SandboxBackend",
    # Constants
    "EntityType",
    "EffectStatus",
    "ExecutionStatus",
    "CALENDAR_DEFAULT_ID",
    "CALENDAR_ALLOWED_STATUSES",
]
