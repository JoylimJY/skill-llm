#!/usr/bin/env python3
"""
Evaluation script for memory-shrink task.
Checks that the agent:
1. Ran session_status and determined context is in the 75-90% band
2. Archived ONLY the correct deletable memory files (not the keep files)
3. Did NOT delete/archive must-keep files
4. Produced a shrink_report.json with required fields
5. Kept summaries of completed tasks (not just deleted everything)
"""
import sys
import json
import os
from pathlib import Path

def load_json(path):
    with open(path) as f:
        return json.load(f)

def run_checks(workspace: str):
    ws = Path(workspace)
    checks = []
    
    # ── Helper ────────────────────────────────────────────────────────────────
    def check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return passed

    # ── CHECK 1: Archive manifest exists and has entries ─────────────────────
    manifest_path = ws / "memory" / "archive" / "manifest.json"
    try:
        manifest = load_json(manifest_path)
        archived_files = [e["file"] for e in manifest]
        check("archive_manifest_exists",
              len(manifest) > 0,
              f"manifest.json found with {len(manifest)} entries: {archived_files}")
    except Exception as e:
        check("archive_manifest_exists", False, f"manifest.json missing or unreadable: {e}")
        manifest = []
        archived_files = []

    # ── CHECK 2: Deletable files were archived ────────────────────────────────
    # Expected deletable: session_history.json, completed_tasks_detail.json,
    #                     expired_tasks.json, old_sprint_notes.json
    deletable = {
        "memory/session_history.json",
        "memory/completed_tasks_detail.json",
        "memory/expired_tasks.json",
        "memory/old_sprint_notes.json",
    }
    
    # Normalize archived_files paths
    archived_normalized = set()
    for f in archived_files:
        # strip leading slash or workspace prefix
        normalized = f.lstrip("/").replace("\\", "/")
        # handle if full absolute path was stored
        if workspace.lstrip("/") in normalized:
            normalized = normalized.replace(workspace.lstrip("/") + "/", "")
        archived_normalized.add(normalized)

    archived_deletable = deletable & archived_normalized
    check("deletable_files_archived",
          len(archived_deletable) >= 3,
          f"Expected >=3 of {deletable} to be archived. Found archived: {archived_deletable}")

    # ── CHECK 3: Must-keep files were NOT archived ─────────────────────────────
    must_keep = {
        "memory/active_discussions.json",
        "memory/team_current_status.json",
    }
    
    # Also check by basename in archive directory
    archive_dir = ws / "memory" / "archive"
    archived_basenames = set()
    if archive_dir.exists():
        archived_basenames = {f.name for f in archive_dir.iterdir() if f.is_file() and f.name != "manifest.json"}
    
    keep_basenames = {"active_discussions.json", "team_current_status.json"}
    wrongly_archived = keep_basenames & archived_basenames
    
    check("must_keep_files_not_archived",
          len(wrongly_archived) == 0,
          f"Must-keep files should NOT be archived. Wrongly archived: {wrongly_archived}")

    # ── CHECK 4: Must-keep files still exist in memory/ ─────────────────────
    keep_exists = []
    keep_missing = []
    for kf in ["active_discussions.json", "team_current_status.json"]:
        p = ws / "memory" / kf
        if p.exists():
            keep_exists.append(kf)
        else:
            keep_missing.append(kf)
    
    check("must_keep_files_still_present",
          len(keep_missing) == 0,
          f"Present: {keep_exists}, Missing: {keep_missing}")

    # ── CHECK 5: Active task files still accessible ──────────────────────────
    active_tasks = ws / "tasks" / "sprint_13" / "active.json"
    try:
        active_data = load_json(active_tasks)
        in_progress = [t for t in active_data if t.get("status") == "in_progress"]
        check("active_tasks_preserved",
              len(in_progress) >= 2,
              f"Active in-progress tasks preserved: {len(in_progress)}")
    except Exception as e:
        check("active_tasks_preserved", False, f"active.json missing or unreadable: {e}")

    # ── CHECK 6: A report file was produced ──────────────────────────────────
    # Look for shrink_report.json anywhere in the workspace
    report_files = list(ws.rglob("shrink_report.json"))
    if not report_files:
        check("shrink_report_exists", False, "shrink_report.json not found anywhere in workspace")
        report = None
    else:
        try:
            report = load_json(report_files[0])
            check("shrink_report_exists", True, f"Found at {report_files[0]}")
        except Exception as e:
            check("shrink_report_exists", False, f"Found but unreadable: {e}")
            report = None

    # ── CHECK 7: Report contains required fields ──────────────────────────────
    if report is not None:
        required_keys_variants = [
            # archived count
            any(k in report for k in ["archived_count", "archived", "num_archived", "files_archived", "archved_count", "items_archived"]),
            # context usage
            any(k in report for k in ["context_usage", "context", "current_context", "context_percent", "context_rate", "usage"]),
            # pending tasks
            any(k in report for k in ["pending_tasks", "pending", "active_tasks", "in_progress_tasks", "outstanding_tasks", "tasks_pending"]),
        ]
        present_count = sum(required_keys_variants)
        check("report_has_required_fields",
              present_count >= 2,
              f"Report keys found: {list(report.keys())}. Required: archived_count, context_usage, pending_tasks. Present: {present_count}/3")
        
        # Check context usage value is plausible (should reference ~82%)
        ctx_val = None
        for k in ["context_usage", "context", "current_context", "context_percent", "context_rate", "usage"]:
            if k in report:
                ctx_val = str(report[k])
                break
        if ctx_val:
            has_numeric = any(c.isdigit() for c in ctx_val)
            check("report_context_value_plausible",
                  has_numeric,
                  f"Context value in report: '{ctx_val}' (should contain numeric context %)")
        else:
            check("report_context_value_plausible", False, "No context usage value found in report")
    else:
        check("report_has_required_fields", False, "No report to evaluate")
        check("report_context_value_plausible", False, "No report to evaluate")

    # ── CHECK 8: Completed task summaries preserved (not just deleted) ────────
    # Either: completed_tasks_detail.json is archived (ok, detail removed)
    # AND some summary reference still exists (in report, or tasks/sprint_12/completed.json untouched)
    sprint12_completed = ws / "tasks" / "sprint_12" / "completed.json"
    try:
        completed_data = load_json(sprint12_completed)
        # The tasks/sprint_12/completed.json should still exist (it's task tracking, not memory detail)
        check("completed_task_summary_preserved",
              len(completed_data) >= 3,
              f"sprint_12/completed.json preserved with {len(completed_data)} task summaries")
    except Exception as e:
        check("completed_task_summary_preserved", False,
              f"sprint_12/completed.json missing or unreadable: {e} — summaries must be preserved")

    # ── CHECK 9: Correct threshold band behavior ──────────────────────────────
    # context=82% → 75-90% band → should archive non-essential but NOT force-skip
    # Evidence: must-keep files are present AND at least some deletion happened
    has_deletions = len(archived_normalized) > 0
    has_kept_critical = len(keep_missing) == 0
    check("correct_threshold_band_behavior",
          has_deletions and has_kept_critical,
          f"82% context (75-90% band): selective archive done={has_deletions}, critical kept={has_kept_critical}")

    # ── Scoring ───────────────────────────────────────────────────────────────
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = round(passed_checks / total_checks, 3)
    overall = passed_checks >= 7  # must pass at least 7 of 9 checks

    return {
        "passed": overall,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        result = run_checks(workspace)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_crash", "passed": False, "detail": str(e)}]
        }
    print(json.dumps(result, indent=2))