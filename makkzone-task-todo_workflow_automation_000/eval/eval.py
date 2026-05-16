import sys
import json
import sqlite3
import subprocess
from pathlib import Path

def run_checks(workspace: str):
    ws = Path(workspace)
    checks = []
    total_score = 0.0

    # ── helper ──────────────────────────────────────────────────────────────
    def add_check(name, passed, detail, weight=1.0):
        nonlocal total_score
        checks.append({"name": name, "passed": passed, "detail": detail})
        if passed:
            total_score += weight

    MAX_SCORE = 8.0  # sum of all weights

    # ── 1. Find tasks.db ────────────────────────────────────────────────────
    db_files = list(ws.rglob("tasks.db"))
    if not db_files:
        add_check("tasks_db_exists", False, "tasks.db not found anywhere in workspace", 1.0)
        # No point continuing DB checks
        summary_check(ws, checks, add_check)
        result = build_result(checks, total_score, MAX_SCORE)
        return result

    db_path = db_files[0]
    add_check("tasks_db_exists", True, f"Found tasks.db at {db_path}", 1.0)

    # ── 2. Connect and read tasks ────────────────────────────────────────────
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM tasks")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
    except Exception as e:
        add_check("db_readable", False, f"Could not read tasks table: {e}", 1.0)
        summary_check(ws, checks, add_check)
        return build_result(checks, total_score, MAX_SCORE)

    add_check("db_readable", True, f"Read {len(rows)} tasks from DB", 1.0)

    # ── 3. All 15 tasks imported ─────────────────────────────────────────────
    total = len(rows)
    add_check(
        "all_tasks_imported",
        total == 15,
        f"Expected 15 tasks, found {total}",
        1.0
    )

    # ── 4. Step 2 — blocked+urgent → in_progress ────────────────────────────
    # Original blocked+urgent tasks: "Security penetration test"
    # (the only row with blocked + urgent in the CSV)
    blocked_urgent_titles = {"Security penetration test"}
    wrong_escalation = []
    for row in rows:
        if row["title"] in blocked_urgent_titles:
            expected_status = "in_progress"
            expected_priority = "urgent"
            if row["status"] != expected_status or row["priority"] != expected_priority:
                wrong_escalation.append(
                    f"'{row['title']}': status={row['status']}, priority={row['priority']}"
                )
    add_check(
        "blocked_urgent_escalated",
        len(wrong_escalation) == 0,
        "OK" if not wrong_escalation else f"Incorrectly escalated: {wrong_escalation}",
        1.5
    )

    # ── 5. Step 3 — pending+low → completed ─────────────────────────────────
    # Original pending+low tasks: "Write API documentation", "Migrate legacy reports",
    # "Data retention policy"
    pending_low_titles = {"Write API documentation", "Migrate legacy reports", "Data retention policy"}
    wrong_archive = []
    for row in rows:
        if row["title"] in pending_low_titles:
            if row["status"] != "completed":
                wrong_archive.append(
                    f"'{row['title']}': status={row['status']} (expected completed)"
                )
    add_check(
        "pending_low_archived",
        len(wrong_archive) == 0,
        "OK" if not wrong_archive else f"Not archived correctly: {wrong_archive}",
        1.5
    )

    # ── 6. Untouched tasks not mutated ───────────────────────────────────────
    # Spot-check: "Fix CORS headers" was already completed+high → should stay
    # "Implement OAuth2 login" was pending+high → should stay pending+high
    untouched = [
        ("Fix CORS headers",       "completed", "high"),
        ("Implement OAuth2 login", "pending",   "high"),
        ("Refactor database layer","pending",   "medium"),
    ]
    mutation_errors = []
    row_by_title = {r["title"]: r for r in rows}
    for title, exp_status, exp_priority in untouched:
        r = row_by_title.get(title)
        if r is None:
            mutation_errors.append(f"'{title}' missing")
        elif r["status"] != exp_status or r["priority"] != exp_priority:
            mutation_errors.append(
                f"'{title}' mutated: status={r['status']} priority={r['priority']}"
            )
    add_check(
        "untouched_tasks_stable",
        len(mutation_errors) == 0,
        "OK" if not mutation_errors else f"Unexpected mutations: {mutation_errors}",
        1.0
    )

    # ── 7. task_summary.json ─────────────────────────────────────────────────
    summary_check(ws, checks, add_check, rows)

    return build_result(checks, total_score, MAX_SCORE)


def summary_check(ws, checks, add_check, db_rows=None):
    summary_files = list(ws.rglob("task_summary.json"))
    if not summary_files:
        add_check("task_summary_exists", False, "task_summary.json not found", 1.0)
        return

    summary_path = summary_files[0]
    try:
        with open(summary_path) as f:
            data = json.load(f)
    except Exception as e:
        add_check("task_summary_valid_json", False, f"Could not parse task_summary.json: {e}", 1.0)
        return

    add_check("task_summary_exists", True, f"Found at {summary_path}", 0.0)

    if db_rows is None:
        add_check("task_summary_counts", False, "Cannot verify counts without DB rows", 1.0)
        return

    # Compute expected counts from actual DB state
    from collections import Counter
    status_counts  = Counter(r["status"]   for r in db_rows)
    priority_counts= Counter(r["priority"] for r in db_rows)

    expected = {
        "total_tasks": len(db_rows),
        "by_status": {
            "pending":     status_counts.get("pending",     0),
            "in_progress": status_counts.get("in_progress", 0),
            "completed":   status_counts.get("completed",   0),
            "blocked":     status_counts.get("blocked",     0),
        },
        "by_priority": {
            "low":    priority_counts.get("low",    0),
            "medium": priority_counts.get("medium", 0),
            "high":   priority_counts.get("high",   0),
            "urgent": priority_counts.get("urgent", 0),
        }
    }

    errors = []
    if data.get("total_tasks") != expected["total_tasks"]:
        errors.append(f"total_tasks: got {data.get('total_tasks')}, expected {expected['total_tasks']}")
    for s in ["pending", "in_progress", "completed", "blocked"]:
        got = (data.get("by_status") or {}).get(s)
        exp = expected["by_status"][s]
        if got != exp:
            errors.append(f"by_status.{s}: got {got}, expected {exp}")
    for p in ["low", "medium", "high", "urgent"]:
        got = (data.get("by_priority") or {}).get(p)
        exp = expected["by_priority"][p]
        if got != exp:
            errors.append(f"by_priority.{p}: got {got}, expected {exp}")

    add_check(
        "task_summary_counts",
        len(errors) == 0,
        "OK" if not errors else f"Count mismatches: {errors}",
        1.0
    )


def build_result(checks, total_score, max_score):
    passed = all(c["passed"] for c in checks)
    score  = round(total_score / max_score, 4)
    return {"passed": passed, "score": score, "checks": checks}


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace)
    print(json.dumps(result, indent=2))