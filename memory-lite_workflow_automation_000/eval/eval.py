#!/usr/bin/env python3
"""Evaluation script for the memory-lite task."""
import json
import sys
import re
from pathlib import Path
from datetime import date

def evaluate(workspace: str) -> dict:
    ws = Path(workspace)
    checks = []
    total_weight = 0
    total_score = 0.0

    def add_check(name: str, passed: bool, detail: str, weight: float = 1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        nonlocal total_weight, total_score
        total_weight += weight
        if passed:
            total_score += weight

    today_str = date.today().isoformat()
    daily_file = ws / "memory" / f"{today_str}.md"
    long_term_file = ws / "MEMORY.md"

    # ── CHECK 1: memory/ directory exists ───────────────────────────────────
    try:
        mem_dir_exists = (ws / "memory").is_dir()
        add_check(
            "memory_directory_exists",
            mem_dir_exists,
            f"'memory/' directory {'found' if mem_dir_exists else 'NOT found'} at {ws / 'memory'}",
            weight=0.5,
        )
    except Exception as e:
        add_check("memory_directory_exists", False, f"Exception: {e}", weight=0.5)

    # ── CHECK 2: daily note file exists for today ────────────────────────────
    try:
        daily_exists = daily_file.exists()
        add_check(
            "daily_note_file_exists",
            daily_exists,
            f"Daily file '{daily_file.name}' {'found' if daily_exists else 'NOT found'}",
            weight=1.0,
        )
    except Exception as e:
        add_check("daily_note_file_exists", False, f"Exception: {e}", weight=1.0)

    # ── CHECK 3: daily note contains at least 2 distinct bullet entries ──────
    try:
        if daily_file.exists():
            content = daily_file.read_text()
            bullets = [l for l in content.splitlines() if l.strip().startswith("- ")]
            has_two_entries = len(bullets) >= 2
            add_check(
                "daily_note_has_multiple_entries",
                has_two_entries,
                f"Found {len(bullets)} bullet entries in daily file (need ≥2). Entries: {bullets}",
                weight=1.5,
            )
        else:
            add_check(
                "daily_note_has_multiple_entries",
                False,
                "Daily file does not exist; cannot check entries.",
                weight=1.5,
            )
    except Exception as e:
        add_check("daily_note_has_multiple_entries", False, f"Exception: {e}", weight=1.5)

    # ── CHECK 4: firmware_bootloader keyword present in a daily note ─────────
    try:
        keyword = "bootloader"
        found_keyword_daily = False
        if (ws / "memory").is_dir():
            for mf in (ws / "memory").glob("*.md"):
                try:
                    if keyword.lower() in mf.read_text().lower():
                        found_keyword_daily = True
                        break
                except Exception:
                    pass
        add_check(
            "daily_note_contains_bootloader_keyword",
            found_keyword_daily,
            f"Keyword '{keyword}' {'found' if found_keyword_daily else 'NOT found'} in memory/*.md",
            weight=1.5,
        )
    except Exception as e:
        add_check("daily_note_contains_bootloader_keyword", False, f"Exception: {e}", weight=1.5)

    # ── CHECK 5: MEMORY.md exists ────────────────────────────────────────────
    try:
        ltm_exists = long_term_file.exists()
        add_check(
            "MEMORY_md_exists",
            ltm_exists,
            f"MEMORY.md {'found' if ltm_exists else 'NOT found'}",
            weight=1.0,
        )
    except Exception as e:
        add_check("MEMORY_md_exists", False, f"Exception: {e}", weight=1.0)

    # ── CHECK 6: MEMORY.md contains the architectural decision entry ─────────
    try:
        arch_keywords = ["CAN bus", "canbus", "can_bus", "CAN-bus", "CANbus"]
        found_arch = False
        arch_detail = "MEMORY.md does not exist."
        if long_term_file.exists():
            ltm_content = long_term_file.read_text()
            for kw in arch_keywords:
                if kw.lower() in ltm_content.lower():
                    found_arch = True
                    arch_detail = f"Found architectural keyword '{kw}' in MEMORY.md"
                    break
            if not found_arch:
                arch_detail = f"None of {arch_keywords} found in MEMORY.md. Content: {ltm_content[:300]}"
        add_check(
            "MEMORY_md_contains_architectural_decision",
            found_arch,
            arch_detail,
            weight=2.0,
        )
    except Exception as e:
        add_check("MEMORY_md_contains_architectural_decision", False, f"Exception: {e}", weight=2.0)

    # ── CHECK 7: summary file exists (memory_summary.md) ────────────────────
    try:
        summary_candidates = list(ws.rglob("memory_summary.md"))
        summary_found = len(summary_candidates) > 0
        add_check(
            "summary_file_exists",
            summary_found,
            f"memory_summary.md {'found at ' + str(summary_candidates[0]) if summary_found else 'NOT found anywhere in workspace'}",
            weight=1.0,
        )
    except Exception as e:
        add_check("summary_file_exists", False, f"Exception: {e}", weight=1.0)

    # ── CHECK 8: summary file contains expected structure ────────────────────
    try:
        summary_candidates = list(ws.rglob("memory_summary.md"))
        if summary_candidates:
            summary_content = summary_candidates[0].read_text()
            has_heading = "# Memory Summary" in summary_content or "## " in summary_content
            has_longterm_section = "long-term" in summary_content.lower() or "long term" in summary_content.lower() or "MEMORY.md" in summary_content or "Long-term" in summary_content
            structural_ok = has_heading and has_longterm_section
            add_check(
                "summary_file_has_structure",
                structural_ok,
                f"Summary has heading: {has_heading}, has long-term section: {has_longterm_section}. Snippet: {summary_content[:400]}",
                weight=1.5,
            )
        else:
            add_check(
                "summary_file_has_structure",
                False,
                "No summary file found to check structure.",
                weight=1.5,
            )
    except Exception as e:
        add_check("summary_file_has_structure", False, f"Exception: {e}", weight=1.5)

    # ── CHECK 9: summary covers at least 3 days of range ────────────────────
    try:
        summary_candidates = list(ws.rglob("memory_summary.md"))
        if summary_candidates:
            summary_content = summary_candidates[0].read_text()
            # Count date-like headings: ## YYYY-MM-DD
            date_headings = re.findall(r"##\s+\d{4}-\d{2}-\d{2}", summary_content)
            covers_three_days = len(date_headings) >= 3
            add_check(
                "summary_covers_3_days",
                covers_three_days,
                f"Found {len(date_headings)} date-headings in summary (need ≥3): {date_headings}",
                weight=1.5,
            )
        else:
            add_check(
                "summary_covers_3_days",
                False,
                "No summary file found.",
                weight=1.5,
            )
    except Exception as e:
        add_check("summary_covers_3_days", False, f"Exception: {e}", weight=1.5)

    # ── Final score ──────────────────────────────────────────────────────────
    score = round(total_score / total_weight, 4) if total_weight > 0 else 0.0
    all_passed = all(c["passed"] for c in checks)

    return {
        "passed": all_passed,
        "score": score,
        "checks": checks,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided."}]}))
        sys.exit(1)
    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))