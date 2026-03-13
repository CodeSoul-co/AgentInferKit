"""
Build image MCQ benchmark from construction safety Excel data.

Steps:
1. Parse test.xlsx to extract descriptions
2. Call DeepSeek API to convert each description into a 4-option MCQ
3. Auto-filter for quality (valid JSON, 4 options, answer in A-D)
4. Output JSONL benchmark file
"""

import json
import os
import re
import sys
import time
from pathlib import Path

import openpyxl
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXCEL_PATH = PROJECT_ROOT / "test.xlsx"
IMAGES_DIR = PROJECT_ROOT / "data" / "uploads" / "images"
OUTPUT_DIR = PROJECT_ROOT / "data" / "benchmark" / "image_mcq"
OUTPUT_FILE = OUTPUT_DIR / "construction_safety_mcq.jsonl"
STATS_FILE = OUTPUT_DIR / "question_stats.json"

API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
API_URL = "https://api.deepseek.com/v1/chat/completions"


def load_excel_data():
    """Parse test.xlsx and return list of (image_path, description)."""
    wb = openpyxl.load_workbook(str(EXCEL_PATH))
    ws = wb.active
    samples = []
    for i, row in enumerate(ws.iter_rows(min_row=1, values_only=True), 1):
        desc = str(row[1]).strip().strip("'") if len(row) > 1 and row[1] else ""
        # Clean up escaped newlines from Excel
        desc = desc.replace("\\n", "\n")
        img_name = f"test_{i:03d}.png"
        img_path = IMAGES_DIR / img_name
        if not img_path.exists():
            print(f"WARNING: image not found: {img_path}")
        samples.append({
            "image": img_name,
            "image_path": str(img_path),
            "description": desc,
        })
    return samples


MCQ_PROMPT = """你是一个建筑施工安全专家。根据以下施工现场安全隐患描述，生成一道四选一选择题。

要求：
1. 题目是一个关于图片中安全隐患的问题（假设考生能看到图片）
2. 正确选项（answer）必须准确概括该隐患的核心问题
3. 三个干扰项必须是同领域但不同类型的安全隐患，要有迷惑性但明确错误
4. 四个选项长度相近，避免正确答案明显偏长
5. 注明题目类型（category）：消防安全/高处作业/危化品管理/用电安全/临时设施/机械设备

隐患描述：
{description}

请严格按以下JSON格式输出，不要输出其他内容：
{{
  "question": "观察图片，该施工现场存在的主要安全隐患是什么？",
  "options": {{
    "A": "选项A内容",
    "B": "选项B内容",
    "C": "选项C内容",
    "D": "选项D内容"
  }},
  "answer": "A",
  "category": "消防安全",
  "explanation": "简要解释为什么正确答案是对的，引用相关规范"
}}"""


def call_llm(description):
    """Call DeepSeek API to generate MCQ from description."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": MCQ_PROMPT.format(description=description)}
        ],
        "temperature": 0.3,
        "max_tokens": 1000,
    }
    resp = requests.post(API_URL, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"].strip()
    return content


def parse_mcq_response(text):
    """Parse LLM response into MCQ dict. Returns None if invalid."""
    # Try to extract JSON from response
    # Strip markdown code fences if present
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON object in text
        m = re.search(r"\{[\s\S]+\}", text)
        if not m:
            return None
        try:
            obj = json.loads(m.group())
        except json.JSONDecodeError:
            return None

    # Validate required fields
    required = ["question", "options", "answer"]
    if not all(k in obj for k in required):
        return None
    opts = obj["options"]
    if not isinstance(opts, dict) or set(opts.keys()) != {"A", "B", "C", "D"}:
        return None
    if obj["answer"] not in ("A", "B", "C", "D"):
        return None
    return obj


def auto_filter(mcq, description):
    """Additional quality checks on generated MCQ."""
    issues = []
    opts = mcq["options"]

    # Check option lengths are roughly similar (no outlier > 2x average)
    lengths = [len(v) for v in opts.values()]
    avg_len = sum(lengths) / len(lengths)
    for k, v in opts.items():
        if len(v) > avg_len * 2.5:
            issues.append(f"Option {k} too long ({len(v)} vs avg {avg_len:.0f})")

    # Check answer option is not empty
    if len(opts[mcq["answer"]].strip()) < 5:
        issues.append("Answer option too short")

    # Check all options are distinct
    opt_texts = list(opts.values())
    if len(set(opt_texts)) < 4:
        issues.append("Duplicate options")

    return issues


def shuffle_options(mcq):
    """Shuffle option positions so answer is not always A."""
    import random
    correct_text = mcq["options"][mcq["answer"]]
    items = list(mcq["options"].values())
    random.shuffle(items)
    labels = ["A", "B", "C", "D"]
    new_opts = dict(zip(labels, items))
    new_answer = labels[items.index(correct_text)]
    mcq["options"] = new_opts
    mcq["answer"] = new_answer
    return mcq


def build_benchmark_sample(idx, sample, mcq):
    """Build a single benchmark JSONL record."""
    mcq = shuffle_options(mcq)
    return {
        "sample_id": f"safety_mcq_{idx:03d}",
        "task_type": "image_mcq",
        "image_path": f"data/uploads/images/{sample['image']}",
        "question": mcq["question"],
        "options": mcq["options"],
        "answer": mcq["answer"],
        "category": mcq.get("category", ""),
        "explanation": mcq.get("explanation", ""),
        "source_description": sample["description"][:200],
    }


def main():
    global API_KEY
    if not API_KEY:
        # Try loading from .env
        env_path = PROJECT_ROOT / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("DEEPSEEK_API_KEY="):
                    API_KEY = line.split("=", 1)[1].strip().strip('"')
                    break
        if not API_KEY:
            print("ERROR: DEEPSEEK_API_KEY not set. Export it or add to .env")
            sys.exit(1)

    print("=== Build Image MCQ Benchmark ===")
    print()

    # Step 1: Load Excel data
    samples = load_excel_data()
    print(f"Loaded {len(samples)} samples from {EXCEL_PATH}")
    print()

    # Step 2 & 3: Generate MCQs via LLM
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    failed = []

    for i, sample in enumerate(samples, 1):
        print(f"[{i}/{len(samples)}] Generating MCQ for {sample['image']}...")
        try:
            raw = call_llm(sample["description"])
            mcq = parse_mcq_response(raw)
            if mcq is None:
                print(f"  FAILED: could not parse LLM response")
                print(f"  Raw: {raw[:200]}")
                failed.append({"index": i, "reason": "parse_error", "raw": raw[:300]})
                continue

            # Step 4: Auto-filter
            issues = auto_filter(mcq, sample["description"])
            if issues:
                print(f"  WARNING: {'; '.join(issues)}")

            record = build_benchmark_sample(i, sample, mcq)
            record["filter_issues"] = issues
            results.append(record)
            print(f"  OK: {mcq['question'][:60]}... answer={mcq['answer']}")

        except Exception as e:
            print(f"  ERROR: {e}")
            failed.append({"index": i, "reason": str(e)})

        time.sleep(0.5)  # Rate limit

    print()
    print(f"Generated: {len(results)}/{len(samples)}, Failed: {len(failed)}")

    # Step 5: Write benchmark JSONL
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for r in results:
            # Remove filter_issues from output (internal only)
            out = {k: v for k, v in r.items() if k != "filter_issues"}
            f.write(json.dumps(out, ensure_ascii=False) + "\n")
    print(f"Benchmark written to: {OUTPUT_FILE}")

    # Step 6: Write question stats
    categories = {}
    for r in results:
        cat = r.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1

    stats = {
        "total_questions": len(results),
        "total_failed": len(failed),
        "categories": categories,
        "answer_distribution": {},
        "failed_details": failed,
    }
    for r in results:
        ans = r["answer"]
        stats["answer_distribution"][ans] = stats["answer_distribution"].get(ans, 0) + 1

    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f"Stats written to: {STATS_FILE}")


if __name__ == "__main__":
    main()
