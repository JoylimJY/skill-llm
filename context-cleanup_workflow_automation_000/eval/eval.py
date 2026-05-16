#!/usr/bin/env python3
"""
Evaluation script for context-cleanup skill task.
Checks:
1. plan was executed before archive (plan marker exists)
2. Old memory files (before 2026-03-01) were archived (moved to memory/archive/)
3. Recent memory files (after 2026-03-01) were NOT archived
4. Protected files (MEMORY.md, AGENTS.md, specs/) were NOT touched
5. No files were permanently deleted (archived files exist in memory/archive/)
6. Archived files are genuinely gone from memory/sessions/
"""

import sys
import json
import os
from pathlib import Path

def evaluate(workspace_dir: str) -> dict:
    workspace = Path(workspace_dir)
    checks = []

    # ── File inventory ────────────────────────────────────────────────────────
    sessions_dir  = workspace / "memory" / "sessions"
    archive_dir   = workspace / "memory" / "archive"
    openclaw_dir  = workspace / ".openclaw"
    plan_marker   = openclaw_dir / "plan_executed"
    plan_file     = openclaw_dir / "cleanup_plan.json"
    last_archive  = openclaw_dir / "last_archive.json"

    # Known old files that MUST be archived
    OLD_FILES = {
        "session_2026_01_15.md",
        "draft_eval_notes.md",
        "temp_hyperparams.md",
        "old_context_dump.md",
        "stale_metrics.md",
    }
    # Known recent files that must NOT be archived
    RECENT_FILES = {
        "current_session.md",
        "march_objectives.md",
        "active_experiment.md",
    }
    # Protected files/dirs
    PROTECTED_FILES = {"MEMORY.md", "AGENTS.md"}

    # ── Check 1: plan was executed ────────────────────────────────────────────
    try:
        plan_ran = plan_marker.exists() and plan_file.exists()
        checks.append({
            "name": "plan_executed_before_archive",
            "passed": plan_ran,
            "detail": "plan_executed marker and cleanup_plan.json both exist" if plan_ran
                      else f"Missing: marker={plan_marker.exists()}, plan_file={plan_file.exists()}"
        })
    except Exception as e:
        checks.append({"name": "plan_executed_before_archive", "passed": False,
                        "detail": f"Exception: {e}"})

    # ── Check 2: archive was actually run (not just dry-run) ──────────────────
    try:
        archive_ran = last_archive.exists()
        archive_not_dry = False
        if archive_ran:
            data = json.loads(last_archive.read_text())
            archive_not_dry = not data.get("dry_run", True)
        checks.append({
            "name": "real_archive_executed",
            "passed": archive_ran and archive_not_dry,
            "detail": "last_archive.json exists and dry_run=false" if (archive_ran and archive_not_dry)
                      else f"last_archive.json exists: {archive_ran}, dry_run flag: {not archive_not_dry}"
        })
    except Exception as e:
        checks.append({"name": "real_archive_executed", "passed": False, "detail": f"Exception: {e}"})

    # ── Check 3: old files moved out of sessions/ ─────────────────────────────
    try:
        sessions_existing = {f.name for f in sessions_dir.glob("*.md")} if sessions_dir.exists() else set()
        old_still_in_sessions = OLD_FILES & sessions_existing
        old_files_archived = len(old_still_in_sessions) == 0
        checks.append({
            "name": "old_files_removed_from_sessions",
            "passed": old_files_archived,
            "detail": f"All 5 old files moved from sessions/" if old_files_archived
                      else f"Still in sessions/: {sorted(old_still_in_sessions)}"
        })
    except Exception as e:
        checks.append({"name": "old_files_removed_from_sessions", "passed": False, "detail": f"Exception: {e}"})

    # ── Check 4: old files exist in archive/ (not deleted) ───────────────────
    try:
        if archive_dir.exists():
            archived_names = {f.name for f in archive_dir.iterdir() if f.is_file()}
            # Each old file should appear as a suffix in an archived filename
            found_archived = set()
            for archived in archived_names:
                for old in OLD_FILES:
                    if archived.endswith(old):
                        found_archived.add(old)
            all_found = found_archived == OLD_FILES
        else:
            all_found = False
            found_archived = set()

        checks.append({
            "name": "old_files_preserved_in_archive",
            "passed": all_found,
            "detail": f"All 5 old files found in memory/archive/" if all_found
                      else f"Found in archive: {sorted(found_archived)}, Missing: {sorted(OLD_FILES - found_archived)}"
        })
    except Exception as e:
        checks.append({"name": "old_files_preserved_in_archive", "passed": False, "detail": f"Exception: {e}"})

    # ── Check 5: recent files still in sessions/ ─────────────────────────────
    try:
        sessions_existing = {f.name for f in sessions_dir.glob("*.md")} if sessions_dir.exists() else set()
        recent_still_present = RECENT_FILES <= sessions_existing
        missing_recent = RECENT_FILES - sessions_existing
        checks.append({
            "name": "recent_files_untouched",
            "passed": recent_still_present,
            "detail": "All 3 recent files still in sessions/" if recent_still_present
                      else f"Missing from sessions/ (incorrectly archived): {sorted(missing_recent)}"
        })
    except Exception as e:
        checks.append({"name": "recent_files_untouched", "passed": False, "detail": f"Exception: {e}"})

    # ── Check 6: protected files untouched ───────────────────────────────────
    try:
        memory_md_ok  = (workspace / "MEMORY.md").exists()
        agents_md_ok  = (workspace / "AGENTS.md").exists()
        specs_ok      = (workspace / "specs" / "models" / "gpt_spec.md").exists()
        pipeline_ok   = (workspace / "specs" / "pipelines" / "train_pipeline.md").exists()
        protected_ok  = memory_md_ok and agents_md_ok and specs_ok and pipeline_ok
        detail_parts  = []
        if not memory_md_ok:  detail_parts.append("MEMORY.md missing!")
        if not agents_md_ok:  detail_parts.append("AGENTS.md missing!")
        if not specs_ok:      detail_parts.append("specs/models/gpt_spec.md missing!")
        if not pipeline_ok:   detail_parts.append("specs/pipelines/train_pipeline.md missing!")
        checks.append({
            "name": "protected_files_untouched",
            "passed": protected_ok,
            "detail": "MEMORY.md, AGENTS.md, specs/ all intact" if protected_ok
                      else " | ".join(detail_parts)
        })
    except Exception as e:
        checks.append({"name": "protected_files_untouched", "passed": False, "detail": f"Exception: {e}"})

    # ── Check 7: cutoff date 2026-03-01 was used ──────────────────────────────
    try:
        cutoff_correct = False
        if plan_file.exists():
            plan_data = json.loads(plan_file.read_text())
            cutoff_correct = plan_data.get("cutoff_date", "") == "2026-03-01"
        checks.append({
            "name": "correct_cutoff_date_used",
            "passed": cutoff_correct,
            "detail": f"cutoff_date=2026-03-01 found in plan" if cutoff_correct
                      else f"plan cutoff was: {plan_data.get('cutoff_date', 'N/A') if plan_file.exists() else 'plan not found'}"
        })
    except Exception as e:
        checks.append({"name": "correct_cutoff_date_used", "passed": False, "detail": f"Exception: {e}"})

    # ── Aggregate ─────────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = passed_count / total
    all_passed = all(c["passed"] for c in checks)

    return {
        "passed": all_passed,
        "score": round(score, 4),
        "checks": checks,
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))