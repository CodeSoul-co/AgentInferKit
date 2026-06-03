"""Shared output paths for experiment artifacts."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
FIGURES = OUTPUTS / "figures"
REPORTS = OUTPUTS / "reports"
METRICS = OUTPUTS / "metrics"
CASES = OUTPUTS / "cases"
LOGS = OUTPUTS / "logs"


def ensure_output_dirs() -> None:
    for directory in [FIGURES, REPORTS, METRICS, CASES, LOGS]:
        directory.mkdir(parents=True, exist_ok=True)
