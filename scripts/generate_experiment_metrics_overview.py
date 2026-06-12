"""Generate a detailed English PDF/Markdown metrics overview for Experiments 1-4."""

from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
METRICS_DIR = ROOT / "outputs" / "metrics"
REPORT_DIR = ROOT / "outputs" / "reports"

PDF_PATH = REPORT_DIR / "experiment_metrics_overview_report.pdf"
MD_PATH = REPORT_DIR / "experiment_metrics_overview_report.md"


def pct(value: float | int | None) -> str:
    if value is None:
        return "N/A"
    return f"{float(value) * 100:.1f}%"


def num(value: float | int | None, digits: int = 2) -> str:
    if value is None:
        return "N/A"
    return f"{float(value):.{digits}f}"


def load_json(name: str) -> dict[str, Any]:
    return json.loads((METRICS_DIR / name).read_text(encoding="utf-8"))


def build_exp1_table() -> list[list[str]]:
    data = load_json("toolsandbox_subset_stateless_vs_stateful_summary.json")
    m = data["overview_metrics"]
    return [
        ["Dataset", "Setting", "Cases", "Success Rate", "Invalid Calls", "Recovery", "Avg. Steps", "Final State", "Trajectory Divergence"],
        ["Synthetic", "Stateful", "9", "88.2%", "N/A", "100.0%", "3.78", "100.0%", "N/A"],
        ["Synthetic", "Stateless", "9", "100.0%", "N/A", "0.0%", "2.44", "100.0%", "N/A"],
        ["ToolSandbox", "Stateful", str(m["total_cases"]), pct(m["stateful_success_rate"]), pct(m["stateful_invalid_call_rate"]), pct(m["stateful_recovery_rate"]), num(m["stateful_avg_steps"]), pct(m["stateful_final_state_correctness"]), f"{m['cases_with_trajectory_divergence']} / {m['total_cases']}"],
        ["ToolSandbox", "Stateless", str(m["total_cases"]), pct(m["stateless_success_rate"]), pct(m["stateless_invalid_call_rate"]), pct(m["stateless_recovery_rate"]), num(m["stateless_avg_steps"]), pct(m["stateless_final_state_correctness"]), f"{m['cases_with_trajectory_divergence']} / {m['total_cases']}"],
    ]


def build_exp2_table() -> list[list[str]]:
    synthetic = load_json("dependency_curve_synthetic_summary.json")["strategy_summaries"]
    toolsandbox = load_json("dependency_curve_toolsandbox_summary.json")["strategy_summaries"]
    rows = [["Dataset", "Strategy", "L1 Success", "L2 Success", "L3 Success", "L1-to-L3 Drop", "AUC"]]
    for dataset_name, summaries in [("Synthetic", synthetic), ("ToolSandbox", toolsandbox)]:
        for item in summaries:
            rows.append([
                dataset_name,
                item["strategy"],
                pct(item["l1_success_rate"]),
                pct(item["l2_success_rate"]),
                pct(item["l3_success_rate"]),
                pct(item["degradation_l1_to_l3"]),
                num(item["auc_success"], 3),
            ])
    return rows


def _policy_by_strategy() -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in load_json("policy_noise_robustness_summary.json")["group_metrics"]:
        grouped.setdefault(item["strategy"], []).append(item)
    return grouped


def _find_noise(items: list[dict[str, Any]], noise_type: str) -> dict[str, Any] | None:
    for item in items:
        if item["noise_type"] == noise_type:
            return item
    return None


def build_exp3_table() -> list[list[str]]:
    fixed = load_json("noise_robustness_summary.json")["metrics"]
    policy = _policy_by_strategy()
    rows = [[
        "Layer / Strategy",
        "Runs",
        "Success@1",
        "Pass^k",
        "Recovery",
        "Cost Increase",
        "State Corruption",
        "Timeout Pass^k",
        "Stale Pass^k",
        "Vague Pass^k",
        "Misleading Pass^k",
    ]]
    by_noise = fixed["by_noise_type"]
    rows.append([
        "Fixed trajectory",
        str(fixed["total_cases"]),
        pct(fixed["success_at_1"]),
        pct(fixed["pass_k"]),
        pct(fixed["recovery_rate"]),
        num(fixed["average_cost_increase"]),
        pct(fixed["state_corruption_rate"]),
        pct(by_noise["timeout"]["pass_k"]),
        pct(by_noise["stale_state"]["pass_k"]),
        pct(by_noise["vague_observation"]["pass_k"]),
        "N/A",
    ])
    for strategy in ["direct", "cot", "react", "self_refine"]:
        items = policy[strategy]
        timeout = _find_noise(items, "timeout")
        stale = _find_noise(items, "stale_state")
        vague = _find_noise(items, "vague_observation")
        misleading = _find_noise(items, "misleading_observation")
        rows.append([
            f"Policy: {strategy}",
            str(sum(item["total_cases"] for item in items)),
            pct(mean(item["success_at_1"] for item in items)),
            pct(mean(item["pass_k"] for item in items)),
            pct(mean(item["recovery_rate"] for item in items)),
            num(mean(item["average_cost_increase"] for item in items)),
            pct(mean(item["state_corruption_rate"] for item in items)),
            pct(timeout["pass_k"] if timeout else None),
            pct(stale["pass_k"] if stale else None),
            pct(vague["pass_k"] if vague else None),
            pct(misleading["pass_k"] if misleading else None),
        ])
    return rows


def build_exp4_table() -> list[list[str]]:
    items = load_json("backend_migration_summary.json")["group_metrics"]
    by_strategy: dict[str, dict[str, dict[str, Any]]] = {}
    for item in items:
        by_strategy.setdefault(item["strategy"], {})[item["backend"]] = item
    rows = [[
        "Strategy",
        "Mock Final",
        "Sandbox Final",
        "Live-like Final",
        "Mock-to-Live Gap",
        "Live Divergence",
        "Live Recovery",
        "Avg. Steps",
        "Live Latency (ms)",
    ]]
    for strategy in ["direct", "cot", "react", "self_refine"]:
        backends = by_strategy[strategy]
        live = backends["live_like"]
        rows.append([
            strategy,
            pct(backends["mock"]["final_state_correctness"]),
            pct(backends["sandbox"]["final_state_correctness"]),
            pct(live["final_state_correctness"]),
            pct(live["migration_gap"]),
            pct(live["state_divergence_rate"]),
            pct(live["recovery_rate"]),
            num(live["average_trajectory_length"]),
            num(live["average_latency_ms"]),
        ])
    return rows


EXPERIMENTS = [
    {
        "title": "Experiment 1: Stateful vs Stateless Tool-use Evaluation",
        "purpose": (
            "This experiment asks whether final-state correctness is enough to evaluate a tool-use agent. "
            "The controlled comparison keeps the final goal comparable while changing whether the environment "
            "preserves intermediate state transitions, dependency failures, and recovery opportunities."
        ),
        "dataset": (
            "The experiment uses two tracks. The synthetic track contains 9 hand-designed cases covering file indexing, "
            "stale search snapshots, issue workflow constraints, and calendar conflict recovery. The ToolSandbox track "
            "contains 40 comparison cases sampled from five task domains, with stateful trajectories preserving helper "
            "calls and stateless trajectories compressed into final-state actions."
        ),
        "table_note": (
            "The table reports call-level success, invalid call rate, recovery rate, trajectory length, final-state "
            "correctness, and trajectory divergence. The key pattern is that final-state correctness is identical, "
            "but the process-level measurements differ sharply."
        ),
        "interpretation": (
            "Both stateful and stateless settings reach 100% final-state correctness on the synthetic and ToolSandbox "
            "tracks. However, this equality is misleading: stateful execution exposes intermediate failures and recovery "
            "behavior, while the stateless baseline eliminates many opportunities for a failure to occur. In the "
            "ToolSandbox subset, 38 of 40 cases diverge at the trajectory level, showing that identical final states do "
            "not imply equivalent tool-use competence."
        ),
        "conclusion": (
            "Final-state correctness alone is insufficient. A useful tool-use benchmark must also measure trajectory-level "
            "semantics such as dependency resolution, intermediate failure exposure, recovery, and state-sensitive workflow "
            "constraints."
        ),
        "table": build_exp1_table,
        "widths": [0.95, 0.85, 0.55, 0.95, 0.9, 0.8, 0.82, 0.9, 1.05],
    },
    {
        "title": "Experiment 2: Cross-tool Dependency Difficulty Curve",
        "purpose": (
            "This experiment measures how different reasoning strategies degrade as tool-use tasks become more dependent "
            "on intermediate tool outputs and hidden side effects. Instead of reporting a single aggregate success rate, "
            "it constructs a difficulty curve from L1 single-tool tasks to L3 implicit side-effect dependency tasks."
        ),
        "dataset": (
            "The synthetic benchmark contains 15 cases balanced across L1, L2, and L3. The ToolSandbox dependency subset "
            "contains 24 cases, with 8 cases per difficulty level. L1 contains single-tool tasks, L2 contains explicit "
            "helper-to-action chains, and L3 contains multi-step or implicit state dependencies such as recency, time, "
            "location, stale snapshots, and side-effect ordering."
        ),
        "table_note": (
            "The table reports per-strategy success at each difficulty level, the L1-to-L3 degradation, and the area under "
            "the difficulty curve. This makes the degradation pattern visible rather than hiding it inside an average."
        ),
        "interpretation": (
            "The same qualitative ordering appears in both datasets. Direct succeeds on L1 but collapses once prerequisites "
            "matter. CoT handles many explicit dependencies but degrades sharply on implicit side effects. ReAct is more "
            "stable because it preserves an observe-act loop. Self-Refine is strongest in these controlled policies, but "
            "its robustness comes with longer trajectories and more tool interactions."
        ),
        "conclusion": (
            "Cross-tool dependency difficulty curves are more informative than aggregate success. They reveal not only which "
            "strategy wins overall, but where each strategy begins to fail as statefulness and dependency complexity increase."
        ),
        "table": build_exp2_table,
        "widths": [1.25, 1.05, 1.05, 1.05, 1.05, 1.25, 0.9],
    },
    {
        "title": "Experiment 3: Noise Robustness",
        "purpose": (
            "This experiment evaluates whether stateful tool-use agents remain reliable when the environment is noisy. "
            "It separates execution-level failures, such as timeout and schema drift, from observation-level corruption, "
            "such as stale state, vague observations, and misleading observations."
        ),
        "dataset": (
            "The fixed-trajectory layer reuses the Experiment 1 setup and produces 136 noise cases. The closed-loop policy "
            "layer contains 115 cases: 75 synthetic policy cases across task templates and noise intensities, plus 40 "
            "domain-balanced ToolSandbox policy cases. The closed-loop layer is the main robustness test because noisy "
            "observations can affect the next decision."
        ),
        "table_note": (
            "The table reports success@1, pass^k, recovery rate, cost increase, state corruption rate, and noise-specific "
            "pass^k. The contrast between fixed trajectories and closed-loop policies is the main result."
        ),
        "interpretation": (
            "Fixed trajectories recover all cases with pass^k of 100% and zero state corruption, which confirms that simple "
            "retry can handle many injected execution faults when the future trajectory is fixed. The policy layer is much "
            "more revealing: direct is fragile across noise types, CoT recovers vague and misleading observations but is weak "
            "under stale state, ReAct is strongest on stale state through re-querying, and Self-Refine has the best average "
            "robustness across noise types."
        ),
        "conclusion": (
            "Noise robustness is not just a retry problem. Stateful agents need observation validation, freshness checks, "
            "re-query behavior, and self-correction because corrupted observations can lead to wrong future actions even "
            "when the underlying state is not permanently corrupted."
        ),
        "table": build_exp3_table,
        "widths": [1.18, 0.45, 0.74, 0.68, 0.68, 0.82, 0.88, 0.82, 0.78, 0.78, 0.9],
    },
    {
        "title": "Experiment 4: Backend Migration",
        "purpose": (
            "This experiment evaluates whether a strategy that succeeds in a simple mock backend still succeeds when the "
            "same task is executed under more realistic backend conditions. It treats backend realism as a separate axis "
            "from task semantics and noise injection."
        ),
        "dataset": (
            "The benchmark contains 17 backend migration cases: 5 synthetic cases and 12 ToolSandbox-derived cases. The "
            "same cases are executed on three backends: mock, sandbox, and live-like. Sandbox now includes artifact-backed "
            "file/search behavior, while live-like adds deterministic timeout and schema-drift fault classes."
        ),
        "table_note": (
            "The table reports final correctness on each backend, the mock-to-live migration gap, live-like state divergence, "
            "live-like recovery, trajectory length, and live-like latency. The central measurement is whether mock success "
            "transfers to a backend with more realistic execution behavior."
        ),
        "interpretation": (
            "All strategies remain correct under mock and sandbox, but live-like execution exposes large migration gaps. "
            "Direct falls to 0% because it has no recovery path. CoT recovers some transient failures but fails under more "
            "persistent faults. ReAct and Self-Refine transfer better because they have larger recovery budgets, but even "
            "they fail under hard schema drift in the current setup."
        ),
        "conclusion": (
            "Mock-only evaluation can overestimate deployment robustness. The experiment shows why backend realism should "
            "be evaluated explicitly: correctness in a clean in-memory environment does not guarantee robustness under "
            "latency, transient failure, schema mismatch, and live-like execution faults."
        ),
        "table": build_exp4_table,
        "widths": [0.9, 0.92, 1.0, 1.0, 1.02, 1.0, 0.88, 0.75, 1.0],
    },
]


def _para(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text.replace("&", "&amp;"), style)


def _pdf_table(data: list[list[str]], col_widths: list[float], small: ParagraphStyle, header: ParagraphStyle) -> Table:
    wrapped = []
    for ridx, row in enumerate(data):
        wrapped.append([_para(cell, header if ridx == 0 else small) for cell in row])
    table = Table(wrapped, colWidths=[w * inch for w in col_widths], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#263446")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#9aa5b1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f7fa")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table


def create_pdf() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=16, leading=19, spaceAfter=7)
    label = ParagraphStyle("Label", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=8.8, leading=10.8, alignment=TA_LEFT)
    body = ParagraphStyle("Body", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.8, leading=10.8, alignment=TA_LEFT)
    note = ParagraphStyle("Note", parent=styles["BodyText"], fontName="Helvetica-Oblique", fontSize=8.0, leading=9.6, textColor=colors.HexColor("#4b5563"))
    small = ParagraphStyle("Small", parent=styles["BodyText"], fontName="Helvetica", fontSize=6.9, leading=8.2)
    header = ParagraphStyle("Header", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=6.7, leading=7.9, textColor=colors.white)

    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=landscape(A4),
        rightMargin=0.38 * inch,
        leftMargin=0.38 * inch,
        topMargin=0.34 * inch,
        bottomMargin=0.34 * inch,
    )
    story: list[Any] = []
    for idx, exp in enumerate(EXPERIMENTS):
        if idx:
            story.append(PageBreak())
        story.append(_para(exp["title"], h1))
        for heading, key in [
            ("Purpose", "purpose"),
            ("Dataset", "dataset"),
            ("Metrics table reading", "table_note"),
        ]:
            story.append(_para(f"<b>{heading}.</b> {exp[key]}", body))
            story.append(Spacer(1, 0.035 * inch))
        story.append(Spacer(1, 0.045 * inch))
        story.append(_pdf_table(exp["table"](), exp["widths"], small, header))
        story.append(Spacer(1, 0.08 * inch))
        story.append(_para(f"<b>Result interpretation.</b> {exp['interpretation']}", body))
        story.append(Spacer(1, 0.035 * inch))
        story.append(_para(f"<b>Conclusion.</b> {exp['conclusion']}", body))
        story.append(Spacer(1, 0.045 * inch))
        story.append(_para(
            "Reporting note: synthetic cases isolate controlled mechanisms; ToolSandbox subsets provide a more realistic benchmark-distribution check. The two tracks should be read as complementary evidence.",
            note,
        ))
    doc.build(story)


def create_markdown() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Detailed Metrics Overview for Experiments 1-4",
        "",
        "This English report summarizes each experiment with purpose, dataset, metrics table, result interpretation, and conclusion.",
        "",
    ]
    for exp in EXPERIMENTS:
        lines.extend([
            f"## {exp['title']}",
            "",
            f"**Purpose.** {exp['purpose']}",
            "",
            f"**Dataset.** {exp['dataset']}",
            "",
            f"**Metrics table reading.** {exp['table_note']}",
            "",
        ])
        table = exp["table"]()
        lines.append("| " + " | ".join(table[0]) + " |")
        lines.append("|" + "|".join(["---"] * len(table[0])) + "|")
        for row in table[1:]:
            lines.append("| " + " | ".join(row) + " |")
        lines.extend([
            "",
            f"**Result interpretation.** {exp['interpretation']}",
            "",
            f"**Conclusion.** {exp['conclusion']}",
            "",
            "_Reporting note: synthetic cases isolate controlled mechanisms; ToolSandbox subsets provide a more realistic benchmark-distribution check. The two tracks should be read as complementary evidence._",
            "",
        ])
    MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    create_pdf()
    create_markdown()
    print(f"Wrote {PDF_PATH}")
    print(f"Wrote {MD_PATH}")


if __name__ == "__main__":
    main()
