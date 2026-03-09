"""Script: Validate and clean a raw dataset, output to data/cleaned/.

Usage:
    python scripts/clean_dataset.py --input data/raw/demo_exam.jsonl --name demo_exam

Steps:
    1. Validate all samples (reject on hard errors).
    2. Auto-fill missing optional fields (split, modality, version, etc.).
    3. Write cleaned JSONL to data/cleaned/{task_type}/{name}.jsonl.
    4. Print validation summary and auto-fill warnings.
"""

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import DATA_DIR
from src.ingest.validator import validate_dataset
from src.ingest.schema_filler import fill_dataset
from src.utils.file_io import read_jsonl, write_jsonl


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate and clean a raw dataset.")
    parser.add_argument("--input", required=True, help="Path to raw JSONL file.")
    parser.add_argument("--name", required=True, help="Dataset name (used for output file).")
    args = parser.parse_args()

    records = read_jsonl(args.input)
    print(f"Loaded {len(records)} samples from {args.input}")

    # Validate
    validation = validate_dataset(records)
    if validation["errors"]:
        print(f"\nValidation FAILED: {validation['error_count']} samples have errors:")
        for err in validation["errors"][:20]:
            print(f"  [{err['sample_id']}] {err['errors']}")
        if validation["error_count"] > 20:
            print(f"  ... and {validation['error_count'] - 20} more")
        sys.exit(1)

    print(f"Validation passed: {validation['valid_count']}/{validation['total']} samples valid")

    if validation["warnings"]:
        print(f"\nWarnings ({len(validation['warnings'])}):")
        for w in validation["warnings"][:20]:
            print(f"  {w}")
        if len(validation["warnings"]) > 20:
            print(f"  ... and {len(validation['warnings']) - 20} more")

    # Fill defaults
    filled, fill_warnings = fill_dataset(records)
    if fill_warnings:
        print(f"\nAuto-fill:")
        for w in fill_warnings:
            print(f"  {w}")

    # Determine task_type for output directory
    task_types = set(r.get("task_type", "unknown") for r in filled)
    if len(task_types) == 1:
        task_type = task_types.pop()
    else:
        task_type = "mixed"

    # Write output
    output_dir = DATA_DIR / "cleaned" / task_type
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{args.name}.jsonl"
    write_jsonl(str(output_path), filled)
    print(f"\nCleaned dataset written to: {output_path}")
    print(f"Total: {len(filled)} samples")


if __name__ == "__main__":
    main()
