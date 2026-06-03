"""Generate Experiment 2 PNG figures and organize output artifacts."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from output_paths import CASES, FIGURES, LOGS, METRICS, OUTPUTS, REPORTS, ensure_output_dirs

LEVELS = ["L1_SINGLE_TOOL", "L2_EXPLICIT_DEP", "L3_IMPLICIT_SIDE_EFFECT"]
LEVEL_LABELS = ["L1\nSingle Tool", "L2\nExplicit Dep.", "L3\nImplicit\nSide Effect"]
STRATEGIES = ["direct", "cot", "react", "self_refine"]
STRATEGY_LABELS = {
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
    _ensure_dirs()
    synthetic = _load_summary("dependency_curve_synthetic_summary.json")
    toolsandbox = _load_summary("dependency_curve_toolsandbox_summary.json")

    _configure_style()
    _plot_success_curve(synthetic, "Synthetic Dependency Curve", FIGURES / "exp2_synthetic_success_curve.png")
    _plot_success_curve(toolsandbox, "ToolSandbox Dependency Curve", FIGURES / "exp2_toolsandbox_success_curve.png")
    _plot_degradation_bars(synthetic, toolsandbox, FIGURES / "exp2_l1_to_l3_degradation.png")
    _plot_metric_heatmap(toolsandbox, FIGURES / "exp2_toolsandbox_metric_heatmap.png")
    _organize_outputs()

    print(f"Wrote figures to {FIGURES}")
    print(f"Organized reports, metrics, cases, and logs under {OUTPUTS}")


def _ensure_dirs() -> None:
    ensure_output_dirs()


def _load_summary(filename: str) -> dict:
    for base in [OUTPUTS, METRICS]:
        path = base / filename
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    raise FileNotFoundError(f"Could not find {filename} in {OUTPUTS} or {METRICS}")


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


def _plot_success_curve(summary: dict, title: str, path: Path) -> None:
    by_key = {
        (metric["strategy"], metric["difficulty_level"]): metric
        for metric in summary["group_metrics"]
    }
    fig, ax = plt.subplots(figsize=(4.8, 3.0))
    x = np.arange(len(LEVELS))
    for strategy in STRATEGIES:
        values = [
            by_key[(strategy, level)]["final_state_correctness"] * 100
            for level in LEVELS
        ]
        ax.plot(
            x,
            values,
            color=COLORS[strategy],
            marker=MARKERS[strategy],
            linewidth=2.0,
            markersize=5,
            label=STRATEGY_LABELS[strategy],
        )
    ax.set_title(title)
    ax.set_ylabel("Final State Correctness (%)")
    ax.set_ylim(-3, 103)
    ax.set_xticks(x, LEVEL_LABELS)
    ax.legend(ncol=2, loc="lower left", fontsize=7)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def _plot_degradation_bars(synthetic: dict, toolsandbox: dict, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(5.0, 3.0))
    x = np.arange(len(STRATEGIES))
    width = 0.36
    synthetic_values = [_summary_by_strategy(synthetic)[s]["degradation_l1_to_l3"] * 100 for s in STRATEGIES]
    toolsandbox_values = [_summary_by_strategy(toolsandbox)[s]["degradation_l1_to_l3"] * 100 for s in STRATEGIES]

    ax.bar(x - width / 2, synthetic_values, width, color="#8FB3D9", label="Synthetic")
    ax.bar(x + width / 2, toolsandbox_values, width, color="#D89C6A", label="ToolSandbox")
    ax.axhline(0, color="#444444", linewidth=0.8)
    ax.set_title("Success Degradation from L1 to L3")
    ax.set_ylabel("Drop in Final State Correctness (pp)")
    ax.set_xticks(x, [STRATEGY_LABELS[s] for s in STRATEGIES])
    ax.legend(loc="upper left", fontsize=7)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def _plot_metric_heatmap(summary: dict, path: Path) -> None:
    metrics = ["final_state_correctness", "dependency_completion_rate", "recovery_rate", "invalid_call_rate"]
    metric_labels = ["Final Correct", "Dep. Complete", "Recovery", "Invalid Calls"]
    rows = []
    row_labels = []
    by_key = {
        (metric["strategy"], metric["difficulty_level"]): metric
        for metric in summary["group_metrics"]
    }
    for strategy in STRATEGIES:
        for level in LEVELS:
            row_labels.append(f"{STRATEGY_LABELS[strategy]} / {level.split('_')[0]}")
            rows.append([by_key[(strategy, level)][metric] * 100 for metric in metrics])

    data = np.array(rows)
    fig, ax = plt.subplots(figsize=(5.2, 4.6))
    image = ax.imshow(data, cmap="YlGnBu", vmin=0, vmax=100, aspect="auto")
    ax.set_title("ToolSandbox Dependency Metrics")
    ax.set_xticks(np.arange(len(metrics)), metric_labels)
    ax.set_yticks(np.arange(len(row_labels)), row_labels)
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            ax.text(j, i, f"{data[i, j]:.0f}", ha="center", va="center", color="#1f2933", fontsize=7)
    cbar = fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Rate (%)")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def _summary_by_strategy(summary: dict) -> dict[str, dict]:
    return {item["strategy"]: item for item in summary["strategy_summaries"]}


def _organize_outputs() -> None:
    for path in list(OUTPUTS.iterdir()):
        if path.is_dir():
            continue
        target_dir = None
        if path.suffix.lower() == ".png":
            target_dir = FIGURES
        elif path.suffix.lower() == ".md":
            target_dir = REPORTS
        elif path.name.endswith("_summary.json"):
            target_dir = METRICS
        elif path.suffix.lower() == ".jsonl":
            target_dir = CASES
        elif path.suffix.lower() == ".log":
            target_dir = LOGS
        if target_dir is not None:
            destination = target_dir / path.name
            if destination.resolve() != path.resolve():
                if destination.exists():
                    destination.unlink()
                shutil.move(str(path), str(destination))


if __name__ == "__main__":
    main()
