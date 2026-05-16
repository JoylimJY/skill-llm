#!/usr/bin/env python3
"""
Evaluation script for the memory-defrag task.
Checks:
1. MEMORY.md was split into focused topical files
2. Stale done-tasks (>14 days) were removed
3. Recent done-tasks (<14 days) were preserved
4. Daily notes (YYYY-MM-DD.md) were preserved (not deleted/modified inappropriately)
5. Recursive nesting (memory/memory/) was deleted
6. Today's daily note contains a defrag log entry
7. File count is in the 15-25 target range (or reasonable)
8. No info was catastrophically lost (key facts still findable)
"""

import sys
import os
import re
import json
from pathlib import Path
from datetime import date, timedelta, datetime

def load_file(path):
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return None

def main(workspace):
    workspace = Path(workspace)
    checks = []
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")

    # ── Helper ────────────────────────────────────────────────────────────────
    def all_md_files():
        return list(workspace.rglob("*.md"))

    def find_content_anywhere(keywords, exclude_daily=True):
        """Search for keywords across all md files."""
        for f in all_md_files():
            if exclude_daily:
                # skip daily notes in check
                if re.match(r"\d{4}-\d{2}-\d{2}\.md$", f.name):
                    continue
            content = load_file(f)
            if content and all(kw.lower() in content.lower() for kw in keywords):
                return True, str(f)
        return False, None

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 1: MEMORY.md was reduced (split into focused files)
    # The original MEMORY.md was 350+ lines covering 10+ topics.
    # After defrag it should be significantly smaller OR split into multiple files.
    # ──────────────────────────────────────────────────────────────────────────
    memory_md_path = workspace / "MEMORY.md"
    memory_md_content = load_file(memory_md_path)
    memory_md_lines = memory_md_content.splitlines() if memory_md_content else []

    # Count all memory-related .md files (not daily notes, not tasks)
    non_daily_non_task_files = []
    for f in all_md_files():
        is_daily = re.match(r"^\d{4}-\d{2}-\d{2}\.md$", f.name)
        is_task = "tasks" in str(f.relative_to(workspace)).split(os.sep)
        is_in_nested_memory = "memory" in str(f.relative_to(workspace)).split(os.sep)[1:] if len(str(f.relative_to(workspace)).split(os.sep)) > 1 else False
        if not is_daily:
            non_daily_non_task_files.append(f)

    # Check that MEMORY.md is reduced OR new focused files exist
    memory_reduced = len(memory_md_lines) < 250  # was ~350 lines
    
    # Count new topical files created in memory/
    topical_files = []
    memory_dir = workspace / "memory"
    if memory_dir.exists():
        for f in memory_dir.iterdir():
            if f.is_file() and f.suffix == ".md":
                is_daily = re.match(r"^\d{4}-\d{2}-\d{2}\.md$", f.name)
                if not is_daily and f.name not in ["notes-2.md", "bm-marketing-ideas.md", "team-contacts.md"]:
                    topical_files.append(f)

    # The agent should have either reduced MEMORY.md significantly or created new split files
    split_happened = memory_reduced or len(topical_files) >= 2
    
    checks.append({
        "name": "MEMORY.md_split_or_reduced",
        "passed": split_happened,
        "detail": f"MEMORY.md now {len(memory_md_lines)} lines (was ~350). New topical files in memory/: {[f.name for f in topical_files]}. Expected splitting of bloated file into focused topics."
    })

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 2: Stale completed tasks (>14 days) were REMOVED
    # setup-hpc-account.md: completed 20 days ago → MUST be gone
    # benchling-renewal.md: completed 18 days ago → MUST be gone
    # ──────────────────────────────────────────────────────────────────────────
    stale_task_1 = workspace / "memory" / "tasks" / "setup-hpc-account.md"
    stale_task_2 = workspace / "memory" / "tasks" / "benchling-renewal.md"

    stale1_removed = not stale_task_1.exists()
    stale2_removed = not stale_task_2.exists()
    stale_tasks_pruned = stale1_removed and stale2_removed

    checks.append({
        "name": "stale_done_tasks_removed_gt14days",
        "passed": stale_tasks_pruned,
        "detail": (
            f"setup-hpc-account.md (20 days old, done) removed: {stale1_removed}. "
            f"benchling-renewal.md (18 days old, done) removed: {stale2_removed}. "
            f"Both tasks with status:done >14 days must be pruned."
        )
    })

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 3: Recent completed tasks (<14 days) were PRESERVED
    # order-neb-reagents.md: completed 5 days ago → MUST exist
    # fix-QuantStudio-calibration.md: completed 3 days ago → MUST exist
    # ──────────────────────────────────────────────────────────────────────────
    recent_task_1 = workspace / "memory" / "tasks" / "order-neb-reagents.md"
    recent_task_2 = workspace / "memory" / "tasks" / "fix-QuantStudio-calibration.md"

    # Also accept that the agent may have moved/renamed these tasks
    # but their content should exist somewhere
    recent1_exists = recent_task_1.exists()
    recent2_exists = recent_task_2.exists()
    
    # Fallback: search content
    if not recent1_exists:
        found, loc = find_content_anywhere(["PO#4421", "neb reagents"], exclude_daily=False)
        if found:
            recent1_exists = True
    if not recent2_exists:
        found, loc = find_content_anywhere(["QuantStudio", "calibration", "done"], exclude_daily=False)
        if found:
            recent2_exists = True

    recent_tasks_kept = recent1_exists and recent2_exists
    checks.append({
        "name": "recent_done_tasks_preserved_lt14days",
        "passed": recent_tasks_kept,
        "detail": (
            f"order-neb-reagents.md (5 days old, done) preserved: {recent1_exists}. "
            f"fix-QuantStudio-calibration.md (3 days old, done) preserved: {recent2_exists}. "
            f"Tasks with status:done <14 days must NOT be pruned."
        )
    })

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 4: Active tasks preserved
    # optimize-delivery-vector.md and enroll-cohort-b.md must remain
    # ──────────────────────────────────────────────────────────────────────────
    active_task_1 = workspace / "memory" / "tasks" / "optimize-delivery-vector.md"
    active_task_2 = workspace / "memory" / "tasks" / "enroll-cohort-b.md"
    
    active1_exists = active_task_1.exists()
    active2_exists = active_task_2.exists()
    
    if not active1_exists:
        found, _ = find_content_anywhere(["delivery vector", "aav"], exclude_daily=False)
        active1_exists = found
    if not active2_exists:
        found, _ = find_content_anywhere(["cohort b", "enroll"], exclude_daily=False)
        active2_exists = found

    checks.append({
        "name": "active_tasks_preserved",
        "passed": active1_exists and active2_exists,
        "detail": (
            f"optimize-delivery-vector.md preserved: {active1_exists}. "
            f"enroll-cohort-b.md preserved: {active2_exists}. "
            f"Active tasks must never be removed."
        )
    })

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 5: Daily notes (YYYY-MM-DD.md) were NOT deleted
    # The past 6 daily notes must still exist
    # ──────────────────────────────────────────────────────────────────────────
    past_dates = [(today - timedelta(days=d)).strftime("%Y-%m-%d") for d in [3, 7, 14, 21, 30, 45]]
    daily_notes_preserved = []
    for d in past_dates:
        note_path = workspace / "memory" / f"{d}.md"
        daily_notes_preserved.append(note_path.exists())
    
    all_daily_preserved = all(daily_notes_preserved)
    checks.append({
        "name": "daily_notes_preserved",
        "passed": all_daily_preserved,
        "detail": (
            f"Past daily notes existence: {list(zip(past_dates, daily_notes_preserved))}. "
            f"All YYYY-MM-DD.md daily notes must be preserved as audit trail."
        )
    })

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 6: Recursive nesting (memory/memory/) was deleted
    # ──────────────────────────────────────────────────────────────────────────
    nested_memory_path = workspace / "memory" / "memory"
    nested_deleted = not nested_memory_path.exists()
    
    checks.append({
        "name": "recursive_nesting_deleted",
        "passed": nested_deleted,
        "detail": (
            f"memory/memory/ directory exists: {nested_memory_path.exists()}. "
            f"Recursive nesting (indexer bug artifact) must be deleted."
        )
    })

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 7: Today's daily note contains a defrag log entry
    # Must have a "Memory Defrag" section with structured info
    # ──────────────────────────────────────────────────────────────────────────
    today_note_path = workspace / "memory" / f"{today_str}.md"
    today_note_content = load_file(today_note_path)
    
    has_defrag_log = False
    has_files_reviewed = False
    has_net_result = False
    defrag_log_detail = "Today's daily note not found"
    
    if today_note_content:
        # Check for Memory Defrag section (case-insensitive)
        has_defrag_log = bool(re.search(r"memory\s+defrag", today_note_content, re.IGNORECASE))
        # Check for structured fields
        has_files_reviewed = bool(re.search(r"files\s+reviewed", today_note_content, re.IGNORECASE))
        has_net_result = bool(re.search(r"net\s+result", today_note_content, re.IGNORECASE))
        defrag_log_detail = (
            f"Has 'Memory Defrag' header: {has_defrag_log}. "
            f"Has 'Files reviewed': {has_files_reviewed}. "
            f"Has 'Net result': {has_net_result}."
        )
    
    defrag_log_complete = has_defrag_log and has_files_reviewed and has_net_result
    checks.append({
        "name": "defrag_log_in_todays_daily_note",
        "passed": defrag_log_complete,
        "detail": defrag_log_detail
    })

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 8: Key information was not catastrophically lost
    # Critical facts must still be findable somewhere in the workspace
    # ──────────────────────────────────────────────────────────────────────────
    key_facts = [
        (["elena vasquez", "crispr"], "Dr. Elena Vasquez key person info"),
        (["gx-7", "phase 2"], "Project Helix GX-7 status"),
        (["vectorco"], "VectorCo vendor relationship"),
        (["ibc-2024-07"], "IBC compliance approval"),
    ]
    
    info_preserved = []
    for keywords, description in key_facts:
        found, loc = find_content_anywhere(keywords, exclude_daily=False)
        info_preserved.append((description, found, loc))
    
    all_info_preserved = all(found for _, found, _ in info_preserved)
    checks.append({
        "name": "critical_information_not_lost",
        "passed": all_info_preserved,
        "detail": str([(desc, found, loc) for desc, found, loc in info_preserved])
    })

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 9: Competitive landscape info was consolidated (not in notes-2.md 
    # with a generic name, or merged appropriately)
    # The agent should have renamed/merged notes-2.md and bm-marketing-ideas.md
    # ──────────────────────────────────────────────────────────────────────────
    bad_names = ["notes-2.md"]
    bad_name_files_remain = []
    for bad_name in bad_names:
        bad_path = workspace / "memory" / bad_name
        if bad_path.exists():
            bad_name_files_remain.append(bad_name)
    
    # Also check whether competitive info is still accessible (just not in a badly-named file)
    comp_info_accessible, comp_loc = find_content_anywhere(["genthera", "meridian bio"], exclude_daily=False)
    
    # Pass if: bad names removed AND competitive info still exists somewhere
    orphan_handled = (len(bad_name_files_remain) == 0) and comp_info_accessible
    checks.append({
        "name": "orphan_files_renamed_or_merged",
        "passed": orphan_handled,
        "detail": (
            f"Poorly-named orphan files still present: {bad_name_files_remain}. "
            f"Competitive info (GenThera, Meridian) still accessible: {comp_info_accessible} at {comp_loc}. "
            f"notes-2.md should be renamed descriptively and content preserved."
        )
    })

    # ──────────────────────────────────────────────────────────────────────────
    # SCORING
    # ──────────────────────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)

    # Hard requirement: the two most critical proprietary-trap checks must pass
    # for overall pass: stale task pruning (14-day rule) + daily note preservation
    hard_checks = [
        "stale_done_tasks_removed_gt14days",
        "recent_done_tasks_preserved_lt14days",
        "daily_notes_preserved",
        "recursive_nesting_deleted",
    ]
    hard_passed = all(
        any(c["name"] == hc and c["passed"] for c in checks)
        for hc in hard_checks
    )

    overall_passed = hard_passed and score >= 0.70

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    main(workspace)