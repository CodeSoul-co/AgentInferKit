"""Script: Export evaluation results as publication-ready figures.

Usage:
    python scripts/export_figures.py --metrics outputs/metrics/exp_001.json --output figures/
    python scripts/export_figures.py --metrics outputs/metrics/exp_001.json outputs/metrics/exp_002.json --output figures/

Generates:
    - accuracy_comparison.png    (bar chart: accuracy by experiment/strategy)
    - token_vs_accuracy.png      (scatter: token cost vs accuracy)
    - by_difficulty.png           (grouped bar: accuracy by difficulty)
    - option_bias.png             (pie chart: option distribution)
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    print("matplotlib is required. Install: pip install matplotlib")
    sys.exit(1)


def load_metrics(paths: List[str]) -> List[Dict[str, Any]]:
    results = []
    for p in paths:
        with open(p, "r", encoding="utf-8") as f:
            results.append(json.load(f))
    return results


def plot_accuracy_comparison(all_metrics: List[Dict[str, Any]], output_dir: Path) -> None:
    labels = []
    accuracies = []
    for m in all_metrics:
        label = f"{m.get('strategy', '?')} ({m.get('model', '?')})"
        labels.append(label)
        accuracies.append(m.get("overall", {}).get("accuracy", 0.0))

    fig, ax = plt.subplots(figsize=(max(6, len(labels) * 1.5), 5))
    bars = ax.bar(labels, accuracies, color="#4C72B0", edgecolor="white")
    for bar, acc in zip(bars, accuracies):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                f"{acc:.2%}", ha="center", va="bottom", fontsize=10)
    ax.set_ylabel("Accuracy")
    ax.set_title("Accuracy Comparison")
    ax.set_ylim(0, 1.1)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output_dir / "accuracy_comparison.png", dpi=150)
    plt.close(fig)
    print(f"  -> {output_dir / 'accuracy_comparison.png'}")


def plot_token_vs_accuracy(all_metrics: List[Dict[str, Any]], output_dir: Path) -> None:
    xs, ys, labels = [], [], []
    for m in all_metrics:
        overall = m.get("overall", {})
        tokens = overall.get("avg_tokens", 0)
        acc = overall.get("accuracy", 0)
        xs.append(tokens)
        ys.append(acc)
        labels.append(m.get("strategy", "?"))

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(xs, ys, s=100, c="#DD8452", edgecolors="white", zorder=3)
    for x, y, label in zip(xs, ys, labels):
        ax.annotate(label, (x, y), textcoords="offset points", xytext=(8, 4), fontsize=9)
    ax.set_xlabel("Avg Tokens")
    ax.set_ylabel("Accuracy")
    ax.set_title("Token Cost vs Accuracy")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output_dir / "token_vs_accuracy.png", dpi=150)
    plt.close(fig)
    print(f"  -> {output_dir / 'token_vs_accuracy.png'}")


def plot_by_difficulty(all_metrics: List[Dict[str, Any]], output_dir: Path) -> None:
    difficulties = ["easy", "medium", "hard"]
    has_data = False
    strategy_data: Dict[str, List[float]] = {}
    for m in all_metrics:
        by_diff = m.get("by_difficulty", {})
        if not by_diff:
            continue
        has_data = True
        label = m.get("strategy", "?")
        strategy_data[label] = [by_diff.get(d, {}).get("accuracy", 0.0) for d in difficulties]

    if not has_data:
        return

    fig, ax = plt.subplots(figsize=(8, 5))
    x = range(len(difficulties))
    width = 0.8 / max(len(strategy_data), 1)
    colors = ["#4C72B0", "#DD8452", "#55A868", "#C44E52"]
    for i, (label, accs) in enumerate(strategy_data.items()):
        offset = (i - len(strategy_data) / 2 + 0.5) * width
        bars = ax.bar([xi + offset for xi in x], accs, width, label=label,
                      color=colors[i % len(colors)], edgecolor="white")
    ax.set_xlabel("Difficulty")
    ax.set_ylabel("Accuracy")
    ax.set_title("Accuracy by Difficulty")
    ax.set_xticks(x)
    ax.set_xticklabels(difficulties)
    ax.set_ylim(0, 1.1)
    ax.legend()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output_dir / "by_difficulty.png", dpi=150)
    plt.close(fig)
    print(f"  -> {output_dir / 'by_difficulty.png'}")


def plot_option_bias(all_metrics: List[Dict[str, Any]], output_dir: Path) -> None:
    # Use first experiment with option_bias data
    for m in all_metrics:
        bias = m.get("option_bias")
        if not bias or not isinstance(bias, dict):
            continue

        labels = list(bias.keys())
        sizes = list(bias.values())
        colors = ["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B2", "#937860"]

        fig, ax = plt.subplots(figsize=(6, 6))
        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, autopct="%1.1f%%",
            colors=colors[:len(labels)], startangle=90
        )
        ax.set_title(f"Option Bias — {m.get('strategy', '?')}")
        fig.tight_layout()
        fig.savefig(output_dir / "option_bias.png", dpi=150)
        plt.close(fig)
        print(f"  -> {output_dir / 'option_bias.png'}")
        return


def main() -> None:
    parser = argparse.ArgumentParser(description="Export evaluation figures.")
    parser.add_argument("--metrics", nargs="+", required=True, help="Paths to metrics JSON files.")
    parser.add_argument("--output", default="figures", help="Output directory for figures.")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    all_metrics = load_metrics(args.metrics)
    print(f"Loaded {len(all_metrics)} experiment(s)")

    plot_accuracy_comparison(all_metrics, output_dir)
    plot_token_vs_accuracy(all_metrics, output_dir)
    plot_by_difficulty(all_metrics, output_dir)
    plot_option_bias(all_metrics, output_dir)

    print("Done.")


if __name__ == "__main__":
    main()
