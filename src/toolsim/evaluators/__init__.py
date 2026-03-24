"""Evaluators for toolsim execution traces and world states."""

from __future__ import annotations

from toolsim.evaluators.evaluator import (
    CallEvaluationResult,
    CallLevelEvaluator,
    StateEvaluationResult,
    StateGoalResult,
    StateLevelEvaluator,
)
from toolsim.evaluators.overview_summary import (
    OverviewMetrics,
    compute_overview_metrics,
    generate_overall_conclusion,
)
from toolsim.evaluators.trajectory_evaluator import (
    TrajectoryComparisonSummary,
    TrajectoryLevelEvaluator,
    TrajectoryMetrics,
    detect_explicit_dependency_resolution,
    detect_overwrite_without_reindex_pattern,
    detect_query_before_index,
    summarize_trajectory_difference,
)

__all__ = [
    # Call-level
    "CallLevelEvaluator",
    "CallEvaluationResult",
    # State-level
    "StateLevelEvaluator",
    "StateEvaluationResult",
    "StateGoalResult",
    # Trajectory-level
    "TrajectoryLevelEvaluator",
    "TrajectoryMetrics",
    "TrajectoryComparisonSummary",
    "detect_query_before_index",
    "detect_explicit_dependency_resolution",
    "detect_overwrite_without_reindex_pattern",
    "summarize_trajectory_difference",
    # Overview
    "OverviewMetrics",
    "compute_overview_metrics",
    "generate_overall_conclusion",
]
