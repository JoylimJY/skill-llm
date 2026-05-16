import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    ws = Path(workspace)
    checks = []

    # ── Helpers ────────────────────────────────────────────────────────────────
    def check(name, passed, detail=""):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return passed

    # ── Locate the custom data directory ──────────────────────────────────────
    project_notes = ws / "project_notes"
    data_log = project_notes / "data.log"
    history_log = project_notes / "history.log"
    export_file = project_notes / "sprint14_export.txt"

    # ── Check 1: data.log exists in project_notes (custom NOTE_TAKER_DIR used) ─
    try:
        exists = data_log.exists()
        check(
            "data.log_in_custom_dir",
            exists,
            f"data.log {'found' if exists else 'NOT found'} at {data_log}"
        )
    except Exception as e:
        check("data.log_in_custom_dir", False, f"Exception: {e}")

    # ── Check 2: All 5 tasks were added ───────────────────────────────────────
    try:
        if data_log.exists():
            raw = data_log.read_text()
        else:
            # Also try history.log as fallback signal
            raw = ""

        # We inspect the history.log for added tasks (even if cleared)
        if history_log.exists():
            history = history_log.read_text()
        else:
            history = ""

        expected_tasks = [
            "Refactor authentication middleware",
            "Write integration tests for payment service",
            "Fix memory leak in worker process",
            "Update API documentation for v2 endpoints",
            "Deploy staging environment for QA team",
        ]
        # All 5 tasks should have been added — check history for "add:" entries
        added_tasks_found = [t for t in expected_tasks if t in history]
        all_added = len(added_tasks_found) == 5
        check(
            "all_five_tasks_added",
            all_added,
            f"Tasks found in history: {added_tasks_found} ({len(added_tasks_found)}/5)"
        )
    except Exception as e:
        check("all_five_tasks_added", False, f"Exception: {e}")

    # ── Check 3: Correct priority assignments recorded in history ─────────────
    try:
        if history_log.exists():
            history = history_log.read_text()
        else:
            history = ""

        priority_checks = {
            "Refactor authentication middleware": "high",
            "Write integration tests for payment service": "low",
            "Fix memory leak in worker process": "high",
            "Deploy staging environment for QA team": "medium",
        }
        priority_ok = []
        for task, level in priority_checks.items():
            # history line looks like: "priority: <task> -> <level>"
            pattern = rf"priority:.*{re.escape(task)}.*{re.escape(level)}"
            if re.search(pattern, history):
                priority_ok.append(task)

        all_priorities = len(priority_ok) == 4
        check(
            "priority_assignments_correct",
            all_priorities,
            f"Correct priority entries: {priority_ok} ({len(priority_ok)}/4)"
        )
    except Exception as e:
        check("priority_assignments_correct", False, f"Exception: {e}")

    # ── Check 4: "Update API documentation" has NO priority assigned ──────────
    try:
        if history_log.exists():
            history = history_log.read_text()
        else:
            history = ""

        no_priority_task = "Update API documentation for v2 endpoints"
        has_priority = bool(re.search(
            rf"priority:.*{re.escape(no_priority_task)}",
            history
        ))
        check(
            "api_docs_task_no_priority",
            not has_priority,
            f"'Update API documentation' priority entry found: {has_priority} (should be False)"
        )
    except Exception as e:
        check("api_docs_task_no_priority", False, f"Exception: {e}")

    # ── Check 5: Two tasks were marked done ───────────────────────────────────
    try:
        if history_log.exists():
            history = history_log.read_text()
        else:
            history = ""

        done_tasks = [
            "Fix memory leak in worker process",
            "Deploy staging environment for QA team",
        ]
        done_found = [t for t in done_tasks if f"done: {t}" in history]
        all_done = len(done_found) == 2
        check(
            "two_tasks_marked_done",
            all_done,
            f"Done entries found: {done_found} ({len(done_found)}/2)"
        )
    except Exception as e:
        check("two_tasks_marked_done", False, f"Exception: {e}")

    # ── Check 6: clear was called (history shows removed items) ───────────────
    try:
        if history_log.exists():
            history = history_log.read_text()
        else:
            history = ""

        cleared = "clear:" in history
        check(
            "clear_was_called",
            cleared,
            f"'clear:' found in history.log: {cleared}"
        )
    except Exception as e:
        check("clear_was_called", False, f"Exception: {e}")

    # ── Check 7: Completed tasks absent from active data.log ──────────────────
    try:
        if data_log.exists():
            active_data = data_log.read_text()
        else:
            active_data = ""

        completed_tasks = [
            "Fix memory leak in worker process",
            "Deploy staging environment for QA team",
        ]
        still_present = [t for t in completed_tasks if t in active_data]
        none_present = len(still_present) == 0
        check(
            "completed_tasks_removed_from_active",
            none_present,
            f"Completed tasks still in data.log: {still_present}"
        )
    except Exception as e:
        check("completed_tasks_removed_from_active", False, f"Exception: {e}")

    # ── Check 8: Active tasks still in data.log ────────────────────────────────
    try:
        if data_log.exists():
            active_data = data_log.read_text()
        else:
            active_data = ""

        remaining_tasks = [
            "Refactor authentication middleware",
            "Write integration tests for payment service",
            "Update API documentation for v2 endpoints",
        ]
        remaining_found = [t for t in remaining_tasks if t in active_data]
        all_remaining = len(remaining_found) == 3
        check(
            "active_tasks_still_present",
            all_remaining,
            f"Active tasks in data.log: {remaining_found} ({len(remaining_found)}/3)"
        )
    except Exception as e:
        check("active_tasks_still_present", False, f"Exception: {e}")

    # ── Check 9: sprint14_export.txt exists in project_notes ─────────────────
    try:
        exists = export_file.exists()
        check(
            "export_file_exists",
            exists,
            f"sprint14_export.txt {'found' if exists else 'NOT found'} at {export_file}"
        )
    except Exception as e:
        check("export_file_exists", False, f"Exception: {e}")

    # ── Check 10: Export file content matches active tasks ────────────────────
    try:
        if export_file.exists():
            export_content = export_file.read_text()
        else:
            export_content = ""

        remaining_tasks = [
            "Refactor authentication middleware",
            "Write integration tests for payment service",
            "Update API documentation for v2 endpoints",
        ]
        export_tasks_found = [t for t in remaining_tasks if t in export_content]
        export_correct = len(export_tasks_found) == 3

        # Also verify completed tasks are NOT in the export
        completed_in_export = [
            t for t in ["Fix memory leak in worker process",
                         "Deploy staging environment for QA team"]
            if t in export_content and "[DONE]" not in export_content
        ]
        # The export is taken after clear, so DONE items should not appear
        done_absent = len([
            t for t in ["Fix memory leak in worker process",
                         "Deploy staging environment for QA team"]
            if t in export_content
        ]) == 0

        export_valid = export_correct and done_absent
        check(
            "export_content_correct",
            export_valid,
            f"Active tasks in export: {export_tasks_found}/3, "
            f"Done tasks absent from export: {done_absent}, "
            f"Export snippet: {export_content[:300]!r}"
        )
    except Exception as e:
        check("export_content_correct", False, f"Exception: {e}")

    # ── Final scoring ──────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4)
    overall = passed_count == total

    return {
        "passed": overall,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))