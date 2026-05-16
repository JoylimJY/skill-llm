#!/usr/bin/env python3
"""
Evaluation script for the neomano-todo fleet backlog cleanup task.

Checks:
1. Stale P3 task (35d old) marked as 'forgotten'
2. Stale P2 task (50d old) marked as 'forgotten'
3. Fresh P3 task (20d old) still 'open'  (NOT forgotten)
4. Fresh P2 task (10d old) still 'open'  (NOT forgotten)
5. Done task still 'done' (not touched incorrectly)
6. P1 compliance task: has due_at set
7. P1 compliance task: has remind_at set
8. P1 compliance task: has cron_job_id set (non-null, non-empty)
9. P1 compliance task: still 'open' status (not accidentally closed)
"""

import sys
import json
import sqlite3
from pathlib import Path

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    checks = []
    passed_all = True

    def add_check(name, passed, detail):
        nonlocal passed_all
        checks.append({"name": name, "passed": passed, "detail": detail})
        if not passed:
            passed_all = False

    # ── Load manifest ────────────────────────────────────────────────────────
    manifest_path = workspace / "ops/.task_manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text())
        db_path = Path(manifest["db_path"])
        id_a = manifest["task_a_id"]  # P3 stale → forgotten
        id_b = manifest["task_b_id"]  # P2 stale → forgotten
        id_c = manifest["task_c_id"]  # P3 fresh → open
        id_d = manifest["task_d_id"]  # P1 compliance → open + dates + cron
        id_e = manifest["task_e_id"]  # P2 fresh → open
        id_f = manifest["task_f_id"]  # done → done
    except Exception as ex:
        add_check("manifest_readable", False, f"Could not read manifest: {ex}")
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    add_check("manifest_readable", True, f"Manifest loaded. DB={db_path}")

    # ── Open DB ──────────────────────────────────────────────────────────────
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
    except Exception as ex:
        add_check("db_accessible", False, f"Cannot open DB: {ex}")
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    add_check("db_accessible", True, f"DB opened at {db_path}")

    def fetch(task_id):
        try:
            return dict(conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone())
        except Exception:
            return None

    # ── Check 1: Task A (P3, 35d) → forgotten ───────────────────────────────
    try:
        row = fetch(id_a)
        if row is None:
            add_check("stale_p3_forgotten", False, f"Task A (id={id_a}) not found in DB.")
        else:
            ok = row["status"] == "forgotten"
            add_check("stale_p3_forgotten",
                      ok,
                      f"Task A ('{row['title']}', P{row['priority']}, 35d old) status={row['status']}; expected 'forgotten'.")
    except Exception as ex:
        add_check("stale_p3_forgotten", False, f"Exception: {ex}")

    # ── Check 2: Task B (P2, 50d) → forgotten ───────────────────────────────
    try:
        row = fetch(id_b)
        if row is None:
            add_check("stale_p2_forgotten", False, f"Task B (id={id_b}) not found in DB.")
        else:
            ok = row["status"] == "forgotten"
            add_check("stale_p2_forgotten",
                      ok,
                      f"Task B ('{row['title']}', P{row['priority']}, 50d old) status={row['status']}; expected 'forgotten'.")
    except Exception as ex:
        add_check("stale_p2_forgotten", False, f"Exception: {ex}")

    # ── Check 3: Task C (P3, 20d) → still open ──────────────────────────────
    try:
        row = fetch(id_c)
        if row is None:
            add_check("fresh_p3_still_open", False, f"Task C (id={id_c}) not found in DB.")
        else:
            ok = row["status"] == "open"
            add_check("fresh_p3_still_open",
                      ok,
                      f"Task C ('{row['title']}', P{row['priority']}, 20d old) status={row['status']}; expected 'open'.")
    except Exception as ex:
        add_check("fresh_p3_still_open", False, f"Exception: {ex}")

    # ── Check 4: Task E (P2, 10d) → still open ──────────────────────────────
    try:
        row = fetch(id_e)
        if row is None:
            add_check("fresh_p2_still_open", False, f"Task E (id={id_e}) not found in DB.")
        else:
            ok = row["status"] == "open"
            add_check("fresh_p2_still_open",
                      ok,
                      f"Task E ('{row['title']}', P{row['priority']}, 10d old) status={row['status']}; expected 'open'.")
    except Exception as ex:
        add_check("fresh_p2_still_open", False, f"Exception: {ex}")

    # ── Check 5: Task F (done) → still done ─────────────────────────────────
    try:
        row = fetch(id_f)
        if row is None:
            add_check("done_task_untouched", False, f"Task F (id={id_f}) not found in DB.")
        else:
            ok = row["status"] == "done"
            add_check("done_task_untouched",
                      ok,
                      f"Task F ('{row['title']}') status={row['status']}; expected 'done'.")
    except Exception as ex:
        add_check("done_task_untouched", False, f"Exception: {ex}")

    # ── Check 6: Task D due_at set ───────────────────────────────────────────
    try:
        row = fetch(id_d)
        if row is None:
            add_check("p1_due_at_set", False, f"Task D (id={id_d}) not found in DB.")
        else:
            ok = bool(row.get("due_at"))
            add_check("p1_due_at_set",
                      ok,
                      f"Task D ('{row['title']}') due_at='{row.get('due_at')}'; expected a non-null value.")
    except Exception as ex:
        add_check("p1_due_at_set", False, f"Exception: {ex}")

    # ── Check 7: Task D remind_at set ───────────────────────────────────────
    try:
        row = fetch(id_d)
        if row is None:
            add_check("p1_remind_at_set", False, f"Task D (id={id_d}) not found in DB.")
        else:
            ok = bool(row.get("remind_at"))
            add_check("p1_remind_at_set",
                      ok,
                      f"Task D ('{row['title']}') remind_at='{row.get('remind_at')}'; expected a non-null value.")
    except Exception as ex:
        add_check("p1_remind_at_set", False, f"Exception: {ex}")

    # ── Check 8: Task D cron_job_id set ─────────────────────────────────────
    try:
        row = fetch(id_d)
        if row is None:
            add_check("p1_cron_job_id_set", False, f"Task D (id={id_d}) not found in DB.")
        else:
            cron = row.get("cron_job_id")
            ok = bool(cron and str(cron).strip())
            add_check("p1_cron_job_id_set",
                      ok,
                      f"Task D cron_job_id='{cron}'; expected a non-empty string (any value simulating a scheduled cron id).")
    except Exception as ex:
        add_check("p1_cron_job_id_set", False, f"Exception: {ex}")

    # ── Check 9: Task D still open ───────────────────────────────────────────
    try:
        row = fetch(id_d)
        if row is None:
            add_check("p1_still_open", False, f"Task D (id={id_d}) not found in DB.")
        else:
            ok = row["status"] == "open"
            add_check("p1_still_open",
                      ok,
                      f"Task D status={row['status']}; expected 'open' (critical compliance task must remain active).")
    except Exception as ex:
        add_check("p1_still_open", False, f"Exception: {ex}")

    conn.close()

    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)

    print(json.dumps({
        "passed": passed_all,
        "score": score,
        "checks": checks
    }, indent=2))


if __name__ == "__main__":
    main()