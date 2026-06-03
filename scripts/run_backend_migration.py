"""Run Experiment 4: backend migration across mock, sandbox, and live-like backends."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from output_paths import CASES, FIGURES, METRICS, REPORTS, ensure_output_dirs  # noqa: E402
from toolsim.runners.backend_migration import (  # noqa: E402
    BACKENDS,
    STRATEGIES,
    BackendMigrationRunner,
    build_backend_migration_cases,
    render_backend_migration_markdown,
)


LABELS = {
    "mock": "Mock",
    "sandbox": "Sandbox",
    "live_like": "Live-like",
    "direct": "Direct",
    "cot": "CoT",
    "react": "ReAct",
    "self_refine": "Self-Refine",
}
COLORS = {
    "direct": "#4C78A8",
    "cot": "#F58518",
    "react": "#54A24B",
    "self_refine": "#B279A2",
}
MARKERS = {
    "direct": "o",
    "cot": "s",
    "react": "^",
    "self_refine": "D",
}


def main() -> None:
    ensure_output_dirs()
    cases = build_backend_migration_cases()
    result = BackendMigrationRunner().run(cases)

    cases_path = CASES / "backend_migration_cases.jsonl"
    with cases_path.open("w", encoding="utf-8") as handle:
        for case in cases:
            handle.write(json.dumps({
                "case_name": case.case_name,
                "source": case.source,
                "description": case.description,
                "target_tool": case.target_tool,
                "live_like_fault": case.live_like_fault,
                "live_like_fault_count": case.live_like_fault_count,
                "goals": case.goals,
                "strategy_tool_calls": case.strategy_tool_calls,
                "initial_state": case.initial_state.to_dict(),
            }, ensure_ascii=False) + "\n")

    summary_path = METRICS / "backend_migration_summary.json"
    summary_path.write_text(json.dumps(result.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")

    report_path = REPORTS / "backend_migration_report.md"
    report_path.write_text(render_backend_migration_markdown(result), encoding="utf-8")

    _write_figures(result.to_dict()["group_metrics"])

    print(f"Wrote {cases_path}")
    print(f"Wrote {summary_path}")
    print(f"Wrote {report_path}")
    print(f"Wrote {FIGURES / 'exp4_backend_migration_curve.png'}")
    print(f"Wrote {FIGURES / 'exp4_backend_migration_gap.png'}")


def _write_figures(group_metrics: list[dict]) -> None:
    _configure_style()
    by_key = {
        (metric["strategy"], metric["backend"]): metric
        for metric in group_metrics
    }
    x = np.arange(len(BACKENDS))

    fig, ax = plt.subplots(figsize=(4.8, 3.0))
    for strategy in STRATEGIES:
        values = [by_key[(strategy, backend)]["final_state_correctness"] * 100 for backend in BACKENDS]
        ax.plot(
            x,
            values,
            color=COLORS[strategy],
            marker=MARKERS[strategy],
            linewidth=2.0,
            markersize=5,
            label=LABELS[strategy],
        )
    ax.set_title("Backend Migration Curve")
    ax.set_ylabel("Final State Correctness (%)")
    ax.set_xticks(x, [LABELS[backend] for backend in BACKENDS])
    ax.set_ylim(-3, 103)
    ax.legend(ncol=2, loc="lower left", fontsize=7)
    fig.tight_layout()
    fig.savefig(FIGURES / "exp4_backend_migration_curve.png", bbox_inches="tight", dpi=300)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(4.8, 3.0))
    gaps = [by_key[(strategy, "live_like")]["migration_gap"] * 100 for strategy in STRATEGIES]
    ax.bar(np.arange(len(STRATEGIES)), gaps, color=[COLORS[strategy] for strategy in STRATEGIES])
    ax.set_title("Mock to Live-like Migration Gap")
    ax.set_ylabel("Final Correctness Drop (pp)")
    ax.set_xticks(np.arange(len(STRATEGIES)), [LABELS[strategy] for strategy in STRATEGIES])
    ax.set_ylim(0, max(gaps) + 10 if gaps else 10)
    fig.tight_layout()
    fig.savefig(FIGURES / "exp4_backend_migration_gap.png", bbox_inches="tight", dpi=300)
    plt.close(fig)


def _configure_style() -> None:
    plt.rcParams.update({
        "figure.dpi": 160,
        "savefig.dpi": 300,
        "font.family": "DejaVu Sans",
        "font.size": 8,
        "axes.titlesize": 9,
        "axes.labelsize": 8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.22,
        "grid.linewidth": 0.7,
        "legend.frameon": False,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
    })


if __name__ == "__main__":
    main()
