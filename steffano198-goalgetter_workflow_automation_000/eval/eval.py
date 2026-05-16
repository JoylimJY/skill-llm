import sys
import json
import re
from pathlib import Path

def run_eval(workspace_str: str):
    checks = []
    home = Path("/root")
    goalgetter_dir = home / ".openclaw" / "goalgetter"
    tasks_file = goalgetter_dir / "tasks.md"
    goals_file = goalgetter_dir / "goals.md"
    done_dir = goalgetter_dir / "done"

    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})

    # ── 1. tasks.md exists ──────────────────────────────────────────────────────
    try:
        tasks_content = tasks_file.read_text()
        add_check("tasks_file_exists", True, f"tasks.md found at {tasks_file}")
    except Exception as e:
        add_check("tasks_file_exists", False, f"tasks.md missing: {e}")
        tasks_content = ""

    # ── 2. tasks.md has the required header ─────────────────────────────────────
    has_header = tasks_content.strip().startswith("# Tasks")
    add_check(
        "tasks_file_header",
        has_header,
        "tasks.md starts with '# Tasks'" if has_header else f"Missing '# Tasks' header. Got: {tasks_content[:60]!r}"
    )

    # ── 3. Pending tasks present (unchecked) ────────────────────────────────────
    required_pending = [
        "Submit manuscript to publisher",
        "Research new article topics",
    ]
    for task_text in required_pending:
        pattern = re.compile(r"-\s*\[\s*\]\s*" + re.escape(task_text), re.IGNORECASE)
        found = bool(pattern.search(tasks_content))
        add_check(
            f"pending_task_present:{task_text}",
            found,
            f"Found unchecked task '{task_text}'" if found else f"Missing unchecked task '{task_text}' in tasks.md"
        )

    # ── 4. "Schedule call with editor" must NOT be in tasks.md as unchecked ─────
    unchecked_editor = re.compile(r"-\s*\[\s*\]\s*Schedule call with editor", re.IGNORECASE)
    editor_unchecked_in_tasks = bool(unchecked_editor.search(tasks_content))
    add_check(
        "completed_task_not_unchecked_in_tasks",
        not editor_unchecked_in_tasks,
        "Correctly removed/completed 'Schedule call with editor' from active unchecked tasks" if not editor_unchecked_in_tasks
        else "ERROR: 'Schedule call with editor' is still unchecked in tasks.md"
    )

    # ── 5. done/ directory exists ────────────────────────────────────────────────
    done_exists = done_dir.is_dir()
    add_check(
        "done_directory_exists",
        done_exists,
        f"done/ directory exists at {done_dir}" if done_exists else f"done/ directory missing at {done_dir}"
    )

    # ── 6. A completed task file exists in done/ containing the editor task ─────
    editor_archived = False
    editor_archive_detail = "No file in done/ mentions 'Schedule call with editor'"
    if done_exists:
        for f in done_dir.rglob("*.md"):
            try:
                content = f.read_text()
                # Must be marked complete with [x]
                if re.search(r"-\s*\[x\]\s*Schedule call with editor", content, re.IGNORECASE):
                    editor_archived = True
                    editor_archive_detail = f"Found completed task in {f.name}"
                    break
            except Exception:
                pass
    add_check(
        "completed_task_archived_in_done",
        editor_archived,
        editor_archive_detail
    )

    # ── 7. goals.md exists ───────────────────────────────────────────────────────
    try:
        goals_content = goals_file.read_text()
        add_check("goals_file_exists", True, f"goals.md found at {goals_file}")
    except Exception as e:
        add_check("goals_file_exists", False, f"goals.md missing: {e}")
        goals_content = ""

    # ── 8. goals.md has the required header ─────────────────────────────────────
    has_goals_header = goals_content.strip().startswith("# Goals")
    add_check(
        "goals_file_header",
        has_goals_header,
        "goals.md starts with '# Goals'" if has_goals_header else f"Missing '# Goals' header. Got: {goals_content[:60]!r}"
    )

    # ── 9. Daily Writing goal section exists with ## heading ────────────────────
    dw_section = re.search(r"^##\s+Daily Writing", goals_content, re.MULTILINE | re.IGNORECASE)
    add_check(
        "daily_writing_section_exists",
        bool(dw_section),
        "Found '## Daily Writing' section" if dw_section else "Missing '## Daily Writing' section in goals.md"
    )

    # ── 10. Daily Writing streak = 4 (3 original + 1 new log entry) ─────────────
    dw_streak_match = None
    if dw_section:
        # Extract content from Daily Writing section until next ## or EOF
        dw_start = dw_section.start()
        next_section = re.search(r"^##\s+", goals_content[dw_start+1:], re.MULTILINE)
        dw_block = goals_content[dw_start: dw_start + 1 + next_section.start()] if next_section else goals_content[dw_start:]
        dw_streak_match = re.search(r"-\s*streak:\s*(\d+)", dw_block)

    dw_streak_val = int(dw_streak_match.group(1)) if dw_streak_match else -1
    dw_streak_ok = dw_streak_val == 4
    add_check(
        "daily_writing_streak_is_4",
        dw_streak_ok,
        f"Daily Writing streak = {dw_streak_val} (expected 4)" if not dw_streak_ok else "Daily Writing streak correctly = 4"
    )

    # ── 11. Daily Writing log contains all 4 dates ──────────────────────────────
    expected_dw_dates = ["2026-03-01", "2026-03-02", "2026-03-03", "2026-03-04"]
    if dw_section:
        dw_start = dw_section.start()
        next_section = re.search(r"^##\s+", goals_content[dw_start+1:], re.MULTILINE)
        dw_block = goals_content[dw_start: dw_start + 1 + next_section.start()] if next_section else goals_content[dw_start:]
    else:
        dw_block = ""

    for d in expected_dw_dates:
        date_present = d in dw_block
        add_check(
            f"daily_writing_log_date:{d}",
            date_present,
            f"Date {d} present in Daily Writing log" if date_present else f"Date {d} MISSING from Daily Writing log"
        )

    # ── 12. Meditation goal section exists ──────────────────────────────────────
    med_section = re.search(r"^##\s+Meditation", goals_content, re.MULTILINE | re.IGNORECASE)
    add_check(
        "meditation_section_exists",
        bool(med_section),
        "Found '## Meditation' section" if med_section else "Missing '## Meditation' section in goals.md"
    )

    # ── 13. Meditation streak = 5 ────────────────────────────────────────────────
    med_streak_val = -1
    if med_section:
        med_start = med_section.start()
        next_med = re.search(r"^##\s+", goals_content[med_start+1:], re.MULTILINE)
        med_block = goals_content[med_start: med_start + 1 + next_med.start()] if next_med else goals_content[med_start:]
        med_streak_match = re.search(r"-\s*streak:\s*(\d+)", med_block)
        med_streak_val = int(med_streak_match.group(1)) if med_streak_match else -1
    else:
        med_block = ""

    med_streak_ok = med_streak_val == 5
    add_check(
        "meditation_streak_is_5",
        med_streak_ok,
        f"Meditation streak = {med_streak_val} (expected 5)" if not med_streak_ok else "Meditation streak correctly = 5"
    )

    # ── 14. Meditation log contains all 5 dates ──────────────────────────────────
    expected_med_dates = ["2026-02-20", "2026-02-21", "2026-02-22", "2026-02-23", "2026-02-24"]
    for d in expected_med_dates:
        date_present = d in med_block
        add_check(
            f"meditation_log_date:{d}",
            date_present,
            f"Date {d} present in Meditation log" if date_present else f"Date {d} MISSING from Meditation log"
        )

    # ── 15. goals.md uses proper indented log entry format (  - YYYY-MM-DD) ──────
    # At least some log entries must match the spec's indented format
    indented_log_entry = re.compile(r"^\s{2}-\s+\d{4}-\d{2}-\d{2}", re.MULTILINE)
    indented_ok = bool(indented_log_entry.search(goals_content))
    add_check(
        "goals_log_entries_properly_indented",
        indented_ok,
        "Log entries use proper '  - YYYY-MM-DD' format" if indented_ok
        else "Log entries do NOT use required '  - YYYY-MM-DD' indented format"
    )

    # ── 16. goals.md uses '- created: YYYY-MM-DD' format for both goals ──────────
    created_lines = re.findall(r"-\s*created:\s*(\d{4}-\d{2}-\d{2})", goals_content)
    created_ok = len(created_lines) >= 2
    add_check(
        "goals_have_created_dates",
        created_ok,
        f"Found {len(created_lines)} '- created:' fields (need >= 2)" if not created_ok
        else f"Both goals have '- created: YYYY-MM-DD' fields"
    )

    # ── 17. goals.md uses '- log:' header marker for both goals ─────────────────
    log_headers = re.findall(r"-\s*log:", goals_content)
    log_ok = len(log_headers) >= 2
    add_check(
        "goals_have_log_headers",
        log_ok,
        f"Found {len(log_headers)} '- log:' header(s) (need >= 2)" if not log_ok
        else "Both goals have '- log:' headers"
    )

    # ── Compute final score ──────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4)
    all_passed = (passed_count == total)

    return {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace_dir)
    print(json.dumps(result, indent=2))