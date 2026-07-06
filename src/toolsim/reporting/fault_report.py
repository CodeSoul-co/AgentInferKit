"""Markdown reports for fault robustness experiments."""

from __future__ import annotations

from pathlib import Path

from toolsim.runners.fault_robustness import FaultRobustnessBatchResult


def render_fault_robustness_markdown(batch_result: FaultRobustnessBatchResult) -> str:
    """Render a fault robustness batch result as Markdown."""
    metrics = batch_result.metrics
    lines = [
        "# Fault Robustness Report",
        "",
        "## Overview",
        f"- Total cases: {metrics.total_cases if metrics else 0}",
        f"- Success@1: {_pct(metrics.success_at_1 if metrics else 0.0)}",
        f"- Pass^k: {_pct(metrics.pass_k if metrics else 0.0)}",
        f"- Success rate: {_pct(metrics.success_rate if metrics else 0.0)}",
        f"- Recovery rate: {_pct(metrics.recovery_rate if metrics else 0.0)}",
        f"- Cost increase: {(metrics.average_cost_increase if metrics else 0.0):.2f} extra calls",
        f"- State corruption rate: {_pct(metrics.state_corruption_rate if metrics else 0.0)}",
        f"- Average extra steps: {(metrics.average_extra_steps if metrics else 0.0):.2f}",
        f"- Average latency increase ms: {(metrics.average_latency_increase_ms if metrics else 0.0):.2f}",
        "",
        "## By Noise Type",
        "",
        "| Noise | Cases | Success@1 | Pass^k | Recovery | Cost increase | State corruption | Latency increase ms |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for noise_type, noise_metrics in (metrics.by_noise_type if metrics else {}).items():
        lines.append(
            "| "
            f"{noise_type} | "
            f"{noise_metrics['total_cases']} | "
            f"{_pct(noise_metrics['success_at_1'])} | "
            f"{_pct(noise_metrics['pass_k'])} | "
            f"{_pct(noise_metrics['recovery_rate'])} | "
            f"{noise_metrics['average_cost_increase']:.2f} | "
            f"{_pct(noise_metrics['state_corruption_rate'])} | "
            f"{noise_metrics['average_latency_increase_ms']:.2f} |"
        )

    lines.extend([
        "",
        "## Cases",
        "",
    ])

    for result in batch_result.results:
        lines.extend([
            f"### {result.case.case_name}",
            "",
            f"- Description: {result.case.description}",
            f"- Noise type: {result.case.noise_type}",
            f"- Source: {result.case.source}",
            f"- Clean success: {result.clean_success}",
            f"- Success@1: {result.success_at_1}",
            f"- Pass^k: {result.pass_k_success}",
            f"- Recovery detected: {result.recovery_detected}",
            f"- State corrupted: {result.state_corrupted}",
            f"- Cost increase: {result.cost_increase}",
            f"- Failed fault calls: {result.failed_fault_calls}",
            f"- Observation fault count: {result.observation_fault_count}",
            f"- Extra steps: {result.extra_steps}",
            f"- Latency increase ms: {result.latency_increase_ms:.2f}",
            f"- Clean sequence: {_sequence(result.clean_result)}",
            f"- Fault sequence: {_sequence(result.fault_result)}",
            "",
        ])

    return "\n".join(lines)


def write_fault_robustness_markdown(batch_result: FaultRobustnessBatchResult, path: str | Path) -> Path:
    """Write a fault robustness report and return the output path."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_fault_robustness_markdown(batch_result), encoding="utf-8")
    return output_path


def _pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def _sequence(result) -> str:
    return " -> ".join(record.tool_name for record in result.trace)
