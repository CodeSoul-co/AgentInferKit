"""Markdown reporting for dependency difficulty-curve experiments."""

from __future__ import annotations

from pathlib import Path

from toolsim.runners.dependency_curve import DependencyCurveResult


def render_dependency_curve_markdown(result: DependencyCurveResult) -> str:
    lines = [
        "# Cross-tool Dependency Difficulty Curve Report",
        "",
        "## Strategy Degradation",
        "",
        "| Strategy | L1 Success | L2 Success | L3 Success | L1->L3 Drop | AUC |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for summary in result.strategy_summaries:
        lines.append(
            f"| {summary.strategy} | {_pct(summary.l1_success_rate)} | {_pct(summary.l2_success_rate)} | "
            f"{_pct(summary.l3_success_rate)} | {_pct(summary.degradation_l1_to_l3)} | "
            f"{summary.auc_success:.3f} |"
        )

    lines.extend([
        "",
        "## Metrics By Difficulty",
        "",
        "| Strategy | Difficulty | Final Correct | Call Success | Invalid Calls | Recovery | Avg Steps | Dependency Completion | Missing Prereq | Side-effect Awareness |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ])
    for metric in result.group_metrics:
        side_effect = "-" if metric.side_effect_awareness_rate is None else _pct(metric.side_effect_awareness_rate)
        lines.append(
            f"| {metric.strategy} | {metric.difficulty_level} | {_pct(metric.final_state_correctness)} | "
            f"{_pct(metric.success_rate)} | {_pct(metric.invalid_call_rate)} | {_pct(metric.recovery_rate)} | "
            f"{metric.average_trajectory_length:.2f} | {_pct(metric.dependency_completion_rate)} | "
            f"{_pct(metric.missing_prerequisite_rate)} | {side_effect} |"
        )

    lines.extend([
        "",
        "## Interpretation",
        _build_interpretation(result),
        "",
    ])
    return "\n".join(lines)


def write_dependency_curve_markdown(result: DependencyCurveResult, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_dependency_curve_markdown(result), encoding="utf-8")
    return output_path


def _build_interpretation(result: DependencyCurveResult) -> str:
    if not result.strategy_summaries:
        return "No strategy results were available."
    ordered = sorted(result.strategy_summaries, key=lambda item: (item.degradation_l1_to_l3, -item.auc_success))
    best = ordered[0]
    worst = ordered[-1]
    return (
        f"The lowest L1-to-L3 degradation is observed for `{best.strategy}`, while `{worst.strategy}` "
        "degrades the most as cross-tool dependencies become implicit and side-effect-driven. "
        "This supports using trajectory-level dependency metrics in addition to final state correctness."
    )


def _pct(value: float) -> str:
    return f"{value * 100:.1f}%"
