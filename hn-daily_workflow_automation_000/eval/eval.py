#!/usr/bin/env python3
"""Evaluation script for the HN Daily tech digest task."""

import json
import sys
from pathlib import Path

def main(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # ── Check 1: Output file exists with correct name ───────────────────────
    output_files = list(workspace.rglob("tech_digest.json"))
    file_found = len(output_files) > 0
    checks.append({
        "name": "Output file 'tech_digest.json' exists",
        "passed": file_found,
        "detail": f"Found {len(output_files)} file(s) named tech_digest.json" if file_found else "No file named tech_digest.json found anywhere in workspace",
    })
    if file_found:
        total_score += 10.0

    if not file_found:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": checks,
        }))
        return

    output_file = output_files[0]

    # ── Check 2: File is valid JSON ──────────────────────────────────────────
    try:
        content = output_file.read_text(encoding="utf-8")
        data = json.loads(content)
        is_valid_json = True
        json_detail = f"Parsed successfully, type={type(data).__name__}"
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        is_valid_json = False
        data = None
        json_detail = f"JSON parse error: {e}"

    checks.append({
        "name": "Output file contains valid JSON",
        "passed": is_valid_json,
        "detail": json_detail,
    })
    if is_valid_json:
        total_score += 10.0

    if not is_valid_json:
        print(json.dumps({
            "passed": False,
            "score": total_score,
            "checks": checks,
        }))
        return

    # ── Check 3: JSON root is an array ───────────────────────────────────────
    is_array = isinstance(data, list)
    checks.append({
        "name": "JSON root is an array of stories",
        "passed": is_array,
        "detail": f"Root type is {type(data).__name__}" if not is_array else "Correct: root is a list",
    })
    if is_array:
        total_score += 10.0
    else:
        print(json.dumps({
            "passed": False,
            "score": total_score,
            "checks": checks,
        }))
        return

    # ── Check 4: Array has at most 5 stories (--limit 5) ─────────────────────
    count = len(data)
    limit_ok = 1 <= count <= 5
    checks.append({
        "name": "Story count respects --limit 5 (between 1 and 5 inclusive)",
        "passed": limit_ok,
        "detail": f"Found {count} stories in output (expected 1–5)",
    })
    if limit_ok:
        total_score += 15.0

    # ── Check 5: All stories have score >= 250 (--min-score 250) ─────────────
    # Identify which stories in the cache pass BOTH keyword filter AND score >= 250
    # Stories from cache that match keyword filter AND score >= 250:
    # 40000001 (OpenAI, score=1423) ✓
    # 40000002 (Python, score=876) ✓  
    # 40000003 (Rust, score=654) ✓
    # 40000004 (GitHub, score=512) ✓
    # 40000005 (Startup, score=389) ✓
    # 40000006 (Machine learning, score=302) ✓
    # 40000007 (Claude, GPT, score=278) ✓
    # 40000008 (LLM, score=245) ✗ (score < 250)
    # 40000009 (ML, score=211) ✗
    # 40000011 (GPT-4o, score=344) ✓
    # 40000013 (neural network, github, score=267) ✓
    # 40000014 (deep learning, score=415) ✓
    # -> 9 stories pass score >= 250 AND keyword filter
    # With --limit 5, we expect exactly 5

    valid_ids_score_250 = {
        40000001, 40000002, 40000003, 40000004, 40000005,
        40000006, 40000007, 40000011, 40000013, 40000014,
    }

    all_scores_ok = True
    score_violations = []
    missing_fields_stories = []

    for i, story in enumerate(data):
        if not isinstance(story, dict):
            all_scores_ok = False
            score_violations.append(f"Item {i} is not a dict")
            continue
        score_val = story.get("score")
        if score_val is None:
            all_scores_ok = False
            score_violations.append(f"Item {i} (id={story.get('id')}) missing 'score' field")
        elif score_val < 250:
            all_scores_ok = False
            score_violations.append(f"Item {i} (id={story.get('id')}, title={story.get('title','?')[:40]}) has score={score_val} < 250")

    checks.append({
        "name": "All stories have score >= 250 (--min-score 250 applied)",
        "passed": all_scores_ok,
        "detail": "All scores pass" if all_scores_ok else "; ".join(score_violations),
    })
    if all_scores_ok:
        total_score += 20.0

    # ── Check 6: Stories have required fields (proprietary JSON schema) ───────
    required_fields = {"id", "title", "url", "score", "by", "descendants", "time"}
    stories_with_all_fields = 0
    for story in data:
        if isinstance(story, dict):
            if required_fields.issubset(story.keys()):
                stories_with_all_fields += 1

    fields_ok = stories_with_all_fields == count and count > 0
    checks.append({
        "name": "Stories contain all required proprietary fields (id, title, url, score, by, descendants, time)",
        "passed": fields_ok,
        "detail": f"{stories_with_all_fields}/{count} stories have all required fields" if count > 0 else "No stories to check",
    })
    if fields_ok:
        total_score += 15.0

    # ── Check 7: Stories are from the known valid set (keyword-filtered) ──────
    story_ids = set()
    for story in data:
        if isinstance(story, dict) and "id" in story:
            story_ids.add(story["id"])

    # All returned IDs should be in the valid set (keyword-matched AND score>=250)
    invalid_ids = story_ids - valid_ids_score_250
    keyword_ok = len(invalid_ids) == 0 and len(story_ids) > 0
    checks.append({
        "name": "Stories pass keyword filter (only tech/AI/programming stories returned)",
        "passed": keyword_ok,
        "detail": (
            f"All {len(story_ids)} story IDs are valid keyword matches"
            if keyword_ok
            else f"Invalid story IDs found (not keyword-matched or score<250): {invalid_ids}"
        ),
    })
    if keyword_ok:
        total_score += 10.0

    # ── Check 8: Correct use of --format json (not text format) ──────────────
    # Text format would contain the emoji header "📰 Hacker News 精选"
    # We check the raw content to ensure it's not text-format output saved as JSON
    raw_content = content.strip()
    not_text_format = "📰" not in raw_content and "Hacker News 精选" not in raw_content
    checks.append({
        "name": "Output uses JSON format (not default text/emoji format)",
        "passed": not_text_format,
        "detail": "Content is clean JSON without text-format decorators" if not_text_format else "Content appears to contain text-format output (emoji headers detected)",
    })
    if not_text_format:
        total_score += 10.0

    # ── Final pass/fail ───────────────────────────────────────────────────────
    # Normalize score to 0-100
    max_score = 100.0
    normalized = min(total_score, max_score)

    # Must pass critical checks: valid JSON array, score filter, and file exists
    critical_passed = file_found and is_valid_json and is_array and all_scores_ok and limit_ok
    passed = critical_passed and normalized >= 70.0

    print(json.dumps({
        "passed": passed,
        "score": round(normalized / 100.0, 3),
        "checks": checks,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "Usage: eval.py <workspace_dir>"}]}))
        sys.exit(1)
    main(sys.argv[1])