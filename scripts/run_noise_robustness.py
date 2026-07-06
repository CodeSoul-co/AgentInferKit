"""Run experiment 3: noise robustness on experiment-1 stateful datasets."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from output_paths import CASES, METRICS, REPORTS, ensure_output_dirs  # noqa: E402
from toolsim.reporting.fault_report import write_fault_robustness_markdown
from toolsim.runners.fault_robustness import (  # noqa: E402
    FaultRobustnessRunner,
    build_experiment1_noise_robustness_cases,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run stateful noise robustness experiments.")
    parser.add_argument(
        "--toolsandbox-path",
        default=str(ROOT / "Toolsandbox" / "tool_sandbox_scenarios.json"),
        help="Path to ToolSandbox JSON data.",
    )
    parser.add_argument(
        "--toolsandbox-per-group",
        type=int,
        default=5,
        help="ToolSandbox comparison subset cases per domain.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(ROOT / "outputs"),
        help="Base output directory. Artifacts are written to reports/metrics/cases subdirectories.",
    )
    args = parser.parse_args()

    output_root = Path(args.output_dir)
    if output_root != ROOT / "outputs":
        reports_dir = output_root / "reports"
        metrics_dir = output_root / "metrics"
        cases_dir = output_root / "cases"
        for directory in [reports_dir, metrics_dir, cases_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    else:
        ensure_output_dirs()
        reports_dir = REPORTS
        metrics_dir = METRICS
        cases_dir = CASES

    cases = build_experiment1_noise_robustness_cases(
        toolsandbox_path=args.toolsandbox_path,
        toolsandbox_per_group=args.toolsandbox_per_group,
    )
    result = FaultRobustnessRunner().run(cases)

    cases_path = cases_dir / "noise_robustness_cases.jsonl"
    with cases_path.open("w", encoding="utf-8") as handle:
        for case in cases:
            handle.write(json.dumps({
                "case_name": case.case_name,
                "description": case.description,
                "noise_type": case.noise_type,
                "source": case.source,
                "k": case.k,
                "clean_tool_calls": case.clean_tool_calls,
                "success_at_1_tool_calls": case.success_at_1_tool_calls or case.fault_tool_calls,
                "pass_k_tool_calls": case.pass_k_tool_calls or case.fault_tool_calls,
                "goals": case.goals,
                "clean_initial_state": case.clean_initial_state.to_dict() if case.clean_initial_state else None,
            }, ensure_ascii=False) + "\n")

    summary_path = metrics_dir / "noise_robustness_summary.json"
    summary_path.write_text(json.dumps(result.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")

    report_path = write_fault_robustness_markdown(
        result,
        reports_dir / "noise_robustness_report.md",
    )

    print(f"Wrote {cases_path}")
    print(f"Wrote {summary_path}")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
