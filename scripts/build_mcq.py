"""Script: Generate MCQ (multiple-choice question) samples from raw data.

Usage:
    python scripts/build_mcq.py --input data/raw/qa_data.jsonl \
                                --output data/processed/datasets/exam_dataset.jsonl \
                                --num_distractors 3
"""
import argparse
import json
import random
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.utils.file_io import read_jsonl, write_jsonl


def main() -> None:
    parser = argparse.ArgumentParser(description="Build MCQ dataset from QA records.")
    parser.add_argument("--input", required=True, help="Path to input JSONL with QA records.")
    parser.add_argument("--output", required=True, help="Path to output JSONL for MCQ samples.")
    parser.add_argument("--num_distractors", type=int, default=3,
                        help="Number of distractor options per question.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    args = parser.parse_args()

    random.seed(args.seed)
    records = read_jsonl(args.input)
    print(f"Loaded {len(records)} records from {args.input}")

    if len(records) < args.num_distractors + 1:
        print(f"Error: Need at least {args.num_distractors + 1} records to build MCQs.")
        sys.exit(1)

    # Collect all reference answers for distractor pool
    all_answers = [r.get("reference_answer", "") for r in records if r.get("reference_answer")]

    mcq_samples: List[Dict[str, Any]] = []
    option_labels = ["A", "B", "C", "D", "E", "F"][:args.num_distractors + 1]

    for i, record in enumerate(records):
        correct_answer = record.get("reference_answer", "")
        if not correct_answer:
            continue

        # Pick distractors from other records
        distractors = [a for a in all_answers if a != correct_answer]
        if len(distractors) < args.num_distractors:
            continue
        selected_distractors = random.sample(distractors, args.num_distractors)

        # Shuffle options
        all_options = [correct_answer] + selected_distractors
        random.shuffle(all_options)
        correct_idx = all_options.index(correct_answer)

        options = {option_labels[j]: all_options[j] for j in range(len(all_options))}
        answer_letter = option_labels[correct_idx]

        mcq_sample = {
            "sample_id": record.get("sample_id", f"mcq_{i:05d}"),
            "task_type": "text_exam",
            "subject": record.get("topic", record.get("subject", "")),
            "question": record.get("question", ""),
            "options": options,
            "answer": answer_letter,
            "explanation": record.get("explanation", ""),
            "metadata": record.get("metadata", {}),
        }
        mcq_samples.append(mcq_sample)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output, mcq_samples)
    print(f"Wrote {len(mcq_samples)} MCQ samples to {args.output}")


if __name__ == "__main__":
    main()
