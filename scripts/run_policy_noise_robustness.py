"""Run experiment 3b: closed-loop agent-policy noise robustness."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from output_paths import METRICS, REPORTS, ensure_output_dirs  # noqa: E402
from toolsim.runners.policy_noise_robustness import (  # noqa: E402
    PolicyNoiseRobustnessRunner,
    build_policy_noise_robustness_cases,
    render_policy_noise_markdown,
)


def main() -> None:
    ensure_output_dirs()

    cases = build_policy_noise_robustness_cases()
    result = PolicyNoiseRobustnessRunner().run(cases)

    summary_path = METRICS / "policy_noise_robustness_summary.json"
    summary_path.write_text(json.dumps(result.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")

    report_path = REPORTS / "policy_noise_robustness_report.md"
    report_path.write_text(render_policy_noise_markdown(result), encoding="utf-8")

    print(f"Wrote {summary_path}")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
