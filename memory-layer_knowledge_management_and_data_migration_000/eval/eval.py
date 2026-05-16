#!/usr/bin/env python3
"""
Evaluation script for the memory-layer migration task.
Checks:
1. Directory structure: memory/topics/ and memory/transcripts/YYYY-MM/ exist
2. Topic files: all 6 legacy topic files migrated to memory/topics/
3. Transcript files: all 4 log files migrated under memory/transcripts/YYYY-MM/ subdirs
4. MEMORY.md rebuilt as Index with correct 7-column table and importance scores
5. MEMORY.md size ≤ 25KB
6. All topic files ≤ 50KB each
7. ~/.openclaw/memory-config.json exists with autoDream.enabled=true and schedule="22:30"
"""

import sys
import json
import re
from pathlib import Path

def run_checks(workspace: str):
    ws = Path(workspace)
    checks = []
    total_score = 0.0
    max_score = 0.0

    def check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        nonlocal total_score, max_score
        max_score += weight
        if passed:
            total_score += weight

    # ── CHECK 1: memory/topics/ directory exists ───────────────────────────────
    topics_dir = ws / "memory" / "topics"
    check(
        "memory/topics/ directory exists",
        topics_dir.is_dir(),
        f"Path: {topics_dir} | exists={topics_dir.is_dir()}",
        weight=0.5
    )

    # ── CHECK 2: memory/transcripts/ has YYYY-MM subdirs ──────────────────────
    transcripts_dir = ws / "memory" / "transcripts"
    has_month_dirs = False
    month_dirs = []
    if transcripts_dir.is_dir():
        month_dirs = [d for d in transcripts_dir.iterdir()
                      if d.is_dir() and re.match(r'^\d{4}-\d{2}$', d.name)]
        has_month_dirs = len(month_dirs) > 0
    check(
        "memory/transcripts/YYYY-MM/ subdirectory structure",
        has_month_dirs,
        f"Found month dirs: {[d.name for d in month_dirs]}",
        weight=0.5
    )

    # ── CHECK 3: Topic files migrated ─────────────────────────────────────────
    expected_topic_keywords = [
        "momentum", "valuation", "stat", "arb", "trend", "var"
    ]
    topic_files = list(topics_dir.glob("*.md")) if topics_dir.is_dir() else []
    topic_names_lower = " ".join(f.stem.lower() for f in topic_files)

    found_topics = 0
    missing_topics = []
    for kw in expected_topic_keywords:
        if kw in topic_names_lower:
            found_topics += 1
        else:
            missing_topics.append(kw)

    # Accept 5 or 6 out of 6 (momentum+alpha could be merged etc)
    topics_ok = found_topics >= 5
    check(
        "Legacy topic files migrated to memory/topics/",
        topics_ok,
        f"Found {found_topics}/6 expected topics. Missing keywords: {missing_topics}. "
        f"Files: {[f.name for f in topic_files]}",
        weight=1.0
    )

    # ── CHECK 4: Topic file size ≤ 50KB each ──────────────────────────────────
    oversized = []
    for tf in topic_files:
        try:
            size = tf.stat().st_size
            if size > 50 * 1024:
                oversized.append(f"{tf.name}({size}B)")
        except Exception as e:
            oversized.append(f"{tf.name}(error:{e})")
    check(
        "All topic files ≤ 50KB",
        len(oversized) == 0,
        f"Oversized files: {oversized}" if oversized else "All topic files within size limit.",
        weight=0.5
    )

    # ── CHECK 5: Log files migrated under transcripts/YYYY-MM/ ───────────────
    if transcripts_dir.is_dir():
        log_files = list(transcripts_dir.rglob("*.log"))
    else:
        log_files = []

    # We expect at least 3 logs (one from 2025-12 might be considered old/archived, but at least 3/4)
    logs_in_month_dirs = [
        lf for lf in log_files
        if lf.parent != transcripts_dir  # must be inside a subdir, not flat
    ]
    check(
        "Log files placed in YYYY-MM subdirectories under memory/transcripts/",
        len(logs_in_month_dirs) >= 3,
        f"Logs in month subdirs: {[str(lf.relative_to(ws)) for lf in logs_in_month_dirs]}",
        weight=1.0
    )

    # ── CHECK 6: MEMORY.md rebuilt as Index with 7-column table ───────────────
    memory_md = ws / "MEMORY.md"
    memory_content = ""
    if memory_md.exists():
        try:
            memory_content = memory_md.read_text(encoding="utf-8")
        except Exception as e:
            check("MEMORY.md readable", False, f"Error: {e}", weight=2.0)
            # Skip further memory checks
            checks_passed = sum(1 for c in checks if c["passed"])
            score = total_score / max_score if max_score > 0 else 0.0
            return {
                "passed": checks_passed == len(checks),
                "score": round(score, 3),
                "checks": checks
            }

    # Must contain the 7 required column headers (Chinese)
    required_columns = ["领域", "主题", "路径", "更新", "摘要", "标签", "重要性"]
    columns_found = [col for col in required_columns if col in memory_content]
    has_all_columns = len(columns_found) == 7
    check(
        "MEMORY.md has all 7 required Index table columns (领域|主题|路径|更新|摘要|标签|重要性)",
        has_all_columns,
        f"Found columns: {columns_found} / Required: {required_columns}",
        weight=2.0
    )

    # Must contain importance scores as floats between 0 and 1
    importance_scores = re.findall(r'\|\s*(0\.\d+|1\.0)\s*\|', memory_content)
    has_importance_scores = len(importance_scores) >= 4  # at least 4 topics indexed
    check(
        "MEMORY.md contains importance scores (0.x float values) for at least 4 entries",
        has_importance_scores,
        f"Found importance scores: {importance_scores}",
        weight=1.5
    )

    # Must reference memory/topics/ paths
    has_topic_paths = "memory/topics/" in memory_content
    check(
        "MEMORY.md references memory/topics/ paths",
        has_topic_paths,
        f"'memory/topics/' found in MEMORY.md: {has_topic_paths}",
        weight=1.0
    )

    # ── CHECK 7: MEMORY.md size ≤ 25KB ────────────────────────────────────────
    if memory_md.exists():
        md_size = memory_md.stat().st_size
        check(
            "MEMORY.md size ≤ 25KB",
            md_size <= 25 * 1024,
            f"MEMORY.md size: {md_size} bytes (limit: {25*1024} bytes)",
            weight=0.5
        )
    else:
        check("MEMORY.md exists", False, "MEMORY.md not found at workspace root.", weight=0.5)

    # ── CHECK 8: ~/.openclaw/memory-config.json with autoDream enabled + schedule ──
    config_path = Path.home() / ".openclaw" / "memory-config.json"
    config_ok = False
    config_detail = ""
    try:
        if config_path.exists():
            raw = config_path.read_text(encoding="utf-8")
            cfg = json.loads(raw)
            ad = cfg.get("autoDream", {})
            enabled = ad.get("enabled", False)
            schedule = ad.get("schedule", "")
            if enabled is True and schedule == "22:30":
                config_ok = True
                config_detail = f"enabled={enabled}, schedule='{schedule}' ✓"
            else:
                config_detail = (
                    f"enabled={enabled} (expected True), "
                    f"schedule='{schedule}' (expected '22:30')"
                )
        else:
            config_detail = f"File not found: {config_path}"
    except json.JSONDecodeError as e:
        config_detail = f"JSON parse error: {e}"
    except Exception as e:
        config_detail = f"Error reading config: {e}"

    check(
        "~/.openclaw/memory-config.json: autoDream.enabled=true, schedule='22:30'",
        config_ok,
        config_detail,
        weight=2.0
    )

    # ── CHECK 9: MEMORY.md no longer contains the old chaotic format ──────────
    old_format_remnants = ["TODO: organize", "DO NOT USE THIS FORMAT", "Last touched: 2026-03-01"]
    still_has_old = any(r in memory_content for r in old_format_remnants)
    check(
        "MEMORY.md old chaotic format removed / fully rewritten",
        not still_has_old,
        f"Old format remnants found: {[r for r in old_format_remnants if r in memory_content]}"
        if still_has_old else "Old format cleanly replaced.",
        weight=0.5
    )

    # ── Final scoring ──────────────────────────────────────────────────────────
    checks_passed = sum(1 for c in checks if c["passed"])
    score = total_score / max_score if max_score > 0 else 0.0
    overall_passed = score >= 0.75  # need 75%+ to pass

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "argument", "passed": False,
                                      "detail": "No workspace path provided."}]}))
        sys.exit(1)

    result = run_checks(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))