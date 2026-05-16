#!/usr/bin/env python3
"""
Evaluation script for the claws-dream memory consolidation task.
Checks:
1. Correct entries archived (entry-001, entry-004, entry-007, entry-009 — all 4)
2. Protected entries NOT archived (entry-002/PIN, entry-003/recent, entry-005/importance,
   entry-006/PERMANENT, entry-008/episode, entry-010/episode)
3. Daily logs marked with <!-- consolidated -->
4. memory/index.json updated: last_consolidated changed from stale date, archived_count >= 5
5. MEMORY.md reduced (archived entries removed or clearly demoted)
"""

import sys
import json
import re
from pathlib import Path
from datetime import datetime, timedelta

def find_workspace(arg):
    return Path(arg)

def run_eval(workspace_str):
    workspace = find_workspace(workspace_str)
    checks = []
    
    TODAY = datetime(2026, 6, 15)
    STALE_DATE = (TODAY - timedelta(days=7)).strftime("%Y-%m-%d")  # 2026-06-08

    # ── Load files ───────────────────────────────────────────────────────────
    memory_md_path = workspace / "MEMORY.md"
    archive_md_path = workspace / "memory/archive.md"
    index_json_path = workspace / "memory/index.json"
    log1_path = workspace / f"memory/2026-06-14.md"
    log2_path = workspace / f"memory/2026-06-13.md"

    def read_safe(path):
        try:
            return path.read_text(encoding="utf-8")
        except Exception as e:
            return None

    memory_text = read_safe(memory_md_path) or ""
    archive_text = read_safe(archive_md_path) or ""
    index_text = read_safe(index_json_path)
    log1_text = read_safe(log1_path) or ""
    log2_text = read_safe(log2_path) or ""

    # ── Parse index.json ─────────────────────────────────────────────────────
    index_data = {}
    if index_text:
        try:
            index_data = json.loads(index_text)
        except Exception:
            index_data = {}

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 1: entry-001 archived
    # Must appear in archive.md and NOT in MEMORY.md active sections
    # ════════════════════════════════════════════════════════════════════════
    entry001_in_archive = "entry-001" in archive_text
    entry001_removed_from_memory = "entry-001" not in memory_text
    c1_passed = entry001_in_archive and entry001_removed_from_memory
    checks.append({
        "name": "entry-001 correctly archived (95 days, importance=0.20, no markers)",
        "passed": c1_passed,
        "detail": (
            f"In archive.md: {entry001_in_archive}, "
            f"Removed from MEMORY.md: {entry001_removed_from_memory}"
        )
    })

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 2: entry-004 archived
    # ════════════════════════════════════════════════════════════════════════
    entry004_in_archive = "entry-004" in archive_text
    entry004_removed_from_memory = "entry-004" not in memory_text
    c2_passed = entry004_in_archive and entry004_removed_from_memory
    checks.append({
        "name": "entry-004 correctly archived (110 days, importance=0.15, no markers)",
        "passed": c2_passed,
        "detail": (
            f"In archive.md: {entry004_in_archive}, "
            f"Removed from MEMORY.md: {entry004_removed_from_memory}"
        )
    })

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 3: entry-007 archived
    # ════════════════════════════════════════════════════════════════════════
    entry007_in_archive = "entry-007" in archive_text
    entry007_removed_from_memory = "entry-007" not in memory_text
    c3_passed = entry007_in_archive and entry007_removed_from_memory
    checks.append({
        "name": "entry-007 correctly archived (92 days, importance=0.25, no markers)",
        "passed": c3_passed,
        "detail": (
            f"In archive.md: {entry007_in_archive}, "
            f"Removed from MEMORY.md: {entry007_removed_from_memory}"
        )
    })

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 4: entry-009 archived
    # HIGH marker doubles base importance: 0.12 * 2 = 0.24 < 0.3, so STILL archived
    # (No PIN, no PERMANENT, not in episodes)
    # ════════════════════════════════════════════════════════════════════════
    entry009_in_archive = "entry-009" in archive_text
    entry009_removed_from_memory = "entry-009" not in memory_text
    c4_passed = entry009_in_archive and entry009_removed_from_memory
    checks.append({
        "name": "entry-009 correctly archived (🔥 HIGH but effective importance 0.24 < 0.3)",
        "passed": c4_passed,
        "detail": (
            f"In archive.md: {entry009_in_archive}, "
            f"Removed from MEMORY.md: {entry009_removed_from_memory}. "
            "Note: HIGH doubles base 0.12 → 0.24, still below threshold 0.3"
        )
    })

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 5: entry-002 (PIN) NOT archived — must remain in MEMORY.md
    # ════════════════════════════════════════════════════════════════════════
    entry002_in_memory = "entry-002" in memory_text
    entry002_wrongly_archived = "entry-002" in archive_text
    c5_passed = entry002_in_memory and not entry002_wrongly_archived
    checks.append({
        "name": "entry-002 (📌 PIN) correctly preserved — exempt from archival",
        "passed": c5_passed,
        "detail": (
            f"Present in MEMORY.md: {entry002_in_memory}, "
            f"Wrongly in archive.md: {entry002_wrongly_archived}"
        )
    })

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 6: entry-006 (PERMANENT) NOT archived — must remain in MEMORY.md
    # ════════════════════════════════════════════════════════════════════════
    entry006_in_memory = "entry-006" in memory_text
    entry006_wrongly_archived = "entry-006" in archive_text
    c6_passed = entry006_in_memory and not entry006_wrongly_archived
    checks.append({
        "name": "entry-006 (⚠️ PERMANENT) correctly preserved — never archive or modify",
        "passed": c6_passed,
        "detail": (
            f"Present in MEMORY.md: {entry006_in_memory}, "
            f"Wrongly in archive.md: {entry006_wrongly_archived}"
        )
    })

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 7: entry-003 NOT archived — only 85 days old (< 90 threshold)
    # ════════════════════════════════════════════════════════════════════════
    entry003_in_memory = "entry-003" in memory_text
    entry003_wrongly_archived = "entry-003" in archive_text
    c7_passed = entry003_in_memory and not entry003_wrongly_archived
    checks.append({
        "name": "entry-003 correctly preserved — only 85 days old (< 90 day threshold)",
        "passed": c7_passed,
        "detail": (
            f"Present in MEMORY.md: {entry003_in_memory}, "
            f"Wrongly in archive.md: {entry003_wrongly_archived}"
        )
    })

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 8: entry-005 NOT archived — importance=0.35 >= 0.3
    # ════════════════════════════════════════════════════════════════════════
    entry005_in_memory = "entry-005" in memory_text
    entry005_wrongly_archived = "entry-005" in archive_text
    c8_passed = entry005_in_memory and not entry005_wrongly_archived
    checks.append({
        "name": "entry-005 correctly preserved — importance 0.35 >= 0.3 threshold",
        "passed": c8_passed,
        "detail": (
            f"Present in MEMORY.md: {entry005_in_memory}, "
            f"Wrongly in archive.md: {entry005_wrongly_archived}"
        )
    })

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 9: entry-008 NOT archived — references episode path
    # ════════════════════════════════════════════════════════════════════════
    entry008_in_memory = "entry-008" in memory_text
    entry008_wrongly_archived = "entry-008" in archive_text
    c9_passed = entry008_in_memory and not entry008_wrongly_archived
    checks.append({
        "name": "entry-008 correctly preserved — linked to episodes/ (exempt from archival)",
        "passed": c9_passed,
        "detail": (
            f"Present in MEMORY.md: {entry008_in_memory}, "
            f"Wrongly in archive.md: {entry008_wrongly_archived}"
        )
    })

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 10: entry-010 NOT archived — referenced episode
    # ════════════════════════════════════════════════════════════════════════
    entry010_in_memory = "entry-010" in memory_text
    entry010_wrongly_archived = "entry-010" in archive_text
    c10_passed = entry010_in_memory and not entry010_wrongly_archived
    checks.append({
        "name": "entry-010 correctly preserved — linked to episodes/ (exempt, even at 200 days)",
        "passed": c10_passed,
        "detail": (
            f"Present in MEMORY.md: {entry010_in_memory}, "
            f"Wrongly in archive.md: {entry010_wrongly_archived}"
        )
    })

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 11: Daily logs marked with <!-- consolidated -->
    # ════════════════════════════════════════════════════════════════════════
    log1_consolidated = "<!-- consolidated -->" in log1_text
    log2_consolidated = "<!-- consolidated -->" in log2_text
    c11_passed = log1_consolidated and log2_consolidated
    checks.append({
        "name": "Daily logs marked with <!-- consolidated --> (not deleted)",
        "passed": c11_passed,
        "detail": (
            f"2026-06-14.md has marker: {log1_consolidated}, "
            f"2026-06-13.md has marker: {log2_consolidated}"
        )
    })

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 12: index.json updated — last_consolidated updated beyond stale date
    # ════════════════════════════════════════════════════════════════════════
    try:
        lc = index_data.get("last_consolidated", "")
        # Should be updated to 2026-06-15 or at least more recent than 2026-06-08
        if lc:
            lc_date = datetime.strptime(lc[:10], "%Y-%m-%d")
            c12_passed = lc_date > datetime.strptime(STALE_DATE, "%Y-%m-%d")
        else:
            c12_passed = False
        detail12 = f"last_consolidated = '{lc}' (was '{STALE_DATE}')"
    except Exception as e:
        c12_passed = False
        detail12 = f"Error parsing last_consolidated: {e}"

    checks.append({
        "name": "index.json last_consolidated updated beyond stale date",
        "passed": c12_passed,
        "detail": detail12
    })

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 13: index.json archived_count reflects newly archived entries
    # Was 1 before, should now be 5 (1 pre-existing + 4 new)
    # ════════════════════════════════════════════════════════════════════════
    try:
        archived_count = index_data.get("archived_count", 0)
        c13_passed = archived_count >= 5
        detail13 = f"archived_count = {archived_count} (expected >= 5)"
    except Exception as e:
        c13_passed = False
        detail13 = f"Error reading archived_count: {e}"

    checks.append({
        "name": "index.json archived_count reflects 4 new archival actions (total >= 5)",
        "passed": c13_passed,
        "detail": detail13
    })

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 14: index.json has health scores with all 5 required metrics
    # ════════════════════════════════════════════════════════════════════════
    try:
        health = index_data.get("health", {})
        required_metrics = {"freshness", "coverage", "coherence", "efficiency", "reachability"}
        has_all_metrics = required_metrics.issubset(set(health.keys()))
        has_overall = "overall" in health
        # All values should be between 0 and 1
        values_valid = all(
            isinstance(health.get(m), (int, float)) and 0.0 <= health.get(m) <= 1.0
            for m in required_metrics
        )
        c14_passed = has_all_metrics and has_overall and values_valid
        detail14 = (
            f"All 5 metrics present: {has_all_metrics}, "
            f"Overall present: {has_overall}, "
            f"Values in [0,1]: {values_valid}. "
            f"Keys found: {list(health.keys())}"
        )
    except Exception as e:
        c14_passed = False
        detail14 = f"Error reading health metrics: {e}"

    checks.append({
        "name": "index.json health section has all 5 required metrics + overall score",
        "passed": c14_passed,
        "detail": detail14
    })

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 15: MEMORY.md total_entries or line count reduced
    # After archiving 4 entries, MEMORY.md should be shorter than original
    # Original was about 80+ lines; after archiving 4 entries it must shrink
    # ════════════════════════════════════════════════════════════════════════
    try:
        memory_lines = len(memory_text.splitlines())
        # Original MEMORY.md had 10 entries × ~8 lines = ~80+ lines
        # After removing 4 entries (~32 lines) it should be < 65 lines
        c15_passed = memory_lines < 70
        detail15 = f"MEMORY.md line count: {memory_lines} (expected < 70 after archiving 4 entries)"
    except Exception as e:
        c15_passed = False
        detail15 = f"Error counting MEMORY.md lines: {e}"

    checks.append({
        "name": "MEMORY.md line count reduced after archiving 4 entries",
        "passed": c15_passed,
        "detail": detail15
    })

    # ════════════════════════════════════════════════════════════════════════
    # Compute final score
    # ════════════════════════════════════════════════════════════════════════
    n_passed = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(n_passed / total, 4)
    passed = n_passed >= 12  # Pass if at least 12/15 checks pass

    return {
        "passed": passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace_dir)
    print(json.dumps(result, indent=2))