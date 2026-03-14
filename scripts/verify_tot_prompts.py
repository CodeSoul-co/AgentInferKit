"""Verify that all tot.yaml files in src/prompts/ have correct BFS fields
and that template variables format without errors."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))

import yaml

BFS_KEYS = {
    "generate_cot",
    "generate_standard",
    "evaluate_value",
    "evaluate_vote",
    "extract_answer",
}

# Each BFS key and the .format() kwargs it must accept
FORMAT_TESTS = {
    "generate_cot":      {"problem": "test problem", "thoughts": ""},
    "generate_standard": {"problem": "test problem", "thoughts": ""},
    "evaluate_value":    {"problem": "test problem", "thoughts": "test reasoning"},
    "evaluate_vote":     {"problem": "test problem", "choices": "Choice 1:\ntest\n"},
    "extract_answer":    {"problem": "test problem", "best_candidate": "test candidate"},
}

PROMPTS_DIR = os.path.join(os.path.dirname(__file__), os.pardir, "src", "prompts")

TOT_FILES = [
    "text_exam/tot.yaml",
    "text_qa/tot.yaml",
    "image_mcq/tot.yaml",
    "api_calling/tot.yaml",
]

all_pass = True

for rel_path in TOT_FILES:
    full_path = os.path.join(PROMPTS_DIR, rel_path)
    print(f"\n=== {rel_path} ===")

    if not os.path.isfile(full_path):
        print(f"  FAIL: file not found")
        all_pass = False
        continue

    with open(full_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    # Check all 5 BFS keys exist
    missing = BFS_KEYS - set(data.keys())
    if missing:
        print(f"  FAIL: missing BFS keys: {missing}")
        all_pass = False
        continue
    print(f"  OK: all 5 BFS keys present")

    # Check each key formats without error
    file_pass = True
    for key in sorted(BFS_KEYS):
        tpl = data[key]
        if not isinstance(tpl, str):
            print(f"  FAIL: {key} is not a string (type={type(tpl).__name__})")
            file_pass = False
            continue
        kwargs = FORMAT_TESTS[key]
        try:
            result = tpl.format(**kwargs)
            # Sanity: result should contain the test values
            assert "test" in result, "formatted result does not contain test data"
            print(f"  OK: {key}.format({', '.join(kwargs.keys())}) succeeded")
        except KeyError as e:
            print(f"  FAIL: {key}.format() raised KeyError: {e}")
            file_pass = False
        except Exception as e:
            print(f"  FAIL: {key}.format() raised {type(e).__name__}: {e}")
            file_pass = False

    if not file_pass:
        all_pass = False

print("\n" + "=" * 50)
if all_pass:
    print("RESULT: ALL PASS")
else:
    print("RESULT: SOME FAILURES")
    sys.exit(1)
