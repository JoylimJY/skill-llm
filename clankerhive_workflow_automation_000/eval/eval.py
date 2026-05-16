#!/usr/bin/env python3
"""
Evaluation script for the ICU coordination task.
Checks:
1. Facts were correctly stored with right keys, values pattern, TTLs, and sources
2. Equipment alerts were popped (claimed), other alerts remain pending
3. Night-shift-handoff task was claimed and released with correct result
4. Old alerts were purged
5. shift_report.json is correct and complete
"""
import sys
import json
import os
import sqlite3
import time
from pathlib import Path

def main(workspace: str):
    checks = []
    
    db_path = os.path.join(workspace, "icu_hive.db")

    # ── Helper ─────────────────────────────────────────────────────────────────
    def add(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return passed

    def get_conn():
        if not os.path.exists(db_path):
            return None
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ── CHECK 0: DB exists ─────────────────────────────────────────────────────
    if not os.path.exists(db_path):
        add("db_exists", False, f"icu_hive.db not found at {db_path}")
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}
    
    add("db_exists", True, f"icu_hive.db found at {db_path}")
    
    conn = get_conn()
    now = time.time()

    # ── CHECK 1a: fact icu.medication_round ───────────────────────────────────
    try:
        row = conn.execute(
            "SELECT value, expires_at, source FROM facts WHERE key='icu.medication_round'"
        ).fetchone()
        if row is None:
            add("fact_medication_round_exists", False, "Key icu.medication_round not found in facts")
        else:
            # Value should be a recent Unix timestamp string (within last 10 minutes)
            try:
                val = float(row["value"])
                val_ok = (now - 600) < val <= (now + 5)
            except Exception:
                val_ok = False
            
            # TTL should give expires_at roughly now + 3600 (within 60s tolerance)
            exp = row["expires_at"]
            ttl_ok = exp is not None and abs(exp - (now + 3600)) < 120
            
            src_ok = row["source"] == "night-shift-intake"
            
            detail = (f"value_ok={val_ok}, ttl_ok={ttl_ok} "
                      f"(expires_at={exp}, expected~{now+3600:.0f}), source_ok={src_ok}")
            add("fact_medication_round_correct", val_ok and ttl_ok and src_ok, detail)
    except Exception as e:
        add("fact_medication_round_correct", False, f"Exception: {e}")

    # ── CHECK 1b: fact icu.ventilator_check ───────────────────────────────────
    try:
        row = conn.execute(
            "SELECT value, expires_at, source FROM facts WHERE key='icu.ventilator_check'"
        ).fetchone()
        if row is None:
            add("fact_ventilator_check_exists", False, "Key icu.ventilator_check not found")
        else:
            try:
                val = float(row["value"])
                val_ok = (now - 600) < val <= (now + 5)
            except Exception:
                val_ok = False
            
            # TTL=1800
            exp = row["expires_at"]
            ttl_ok = exp is not None and abs(exp - (now + 1800)) < 120
            
            src_ok = row["source"] == "night-shift-intake"
            detail = f"value_ok={val_ok}, ttl_ok={ttl_ok} (expires_at={exp}), source_ok={src_ok}"
            add("fact_ventilator_check_correct", val_ok and ttl_ok and src_ok, detail)
    except Exception as e:
        add("fact_ventilator_check_correct", False, f"Exception: {e}")

    # ── CHECK 1c: fact icu.patient_census ─────────────────────────────────────
    try:
        row = conn.execute(
            "SELECT value, expires_at, source FROM facts WHERE key='icu.patient_census'"
        ).fetchone()
        if row is None:
            add("fact_patient_census_exists", False, "Key icu.patient_census not found")
        else:
            val_ok = row["value"] == "14"
            exp = row["expires_at"]
            ttl_ok = exp is not None and abs(exp - (now + 7200)) < 120
            src_ok = row["source"] == "night-shift-intake"
            detail = f"value_ok={val_ok} (got {row['value']!r}), ttl_ok={ttl_ok}, source_ok={src_ok}"
            add("fact_patient_census_correct", val_ok and ttl_ok and src_ok, detail)
    except Exception as e:
        add("fact_patient_census_correct", False, f"Exception: {e}")

    # ── CHECK 1d: fact icu.code_blue_protocol ─────────────────────────────────
    try:
        row = conn.execute(
            "SELECT value, expires_at, source FROM facts WHERE key='icu.code_blue_protocol'"
        ).fetchone()
        if row is None:
            add("fact_code_blue_exists", False, "Key icu.code_blue_protocol not found")
        else:
            val_ok = row["value"] == "active"
            # No TTL — expires_at must be NULL
            no_ttl = row["expires_at"] is None
            src_ok = row["source"] == "night-shift-intake"
            detail = f"value_ok={val_ok}, no_ttl={no_ttl} (expires_at={row['expires_at']}), source_ok={src_ok}"
            add("fact_code_blue_correct", val_ok and no_ttl and src_ok, detail)
    except Exception as e:
        add("fact_code_blue_correct", False, f"Exception: {e}")

    # ── CHECK 2: Equipment alerts were popped (claimed), others pending ────────
    try:
        # The 2 equipment alerts queued in step 2 should be claimed
        eq_alerts = conn.execute(
            "SELECT message, claimed FROM alerts WHERE topic='equipment' AND claimed=1"
            " AND message != 'IV pump calibration overdue — unresolved handoff'"
        ).fetchall()
        
        expected_msgs = {
            "Defibrillator unit DEF-3 requires recalibration before 02:00",
            "Suction pump in Room 4 is making abnormal noise — inspect before use"
        }
        
        found_msgs = {r["message"] for r in eq_alerts if r["claimed"] == 1}
        both_popped = expected_msgs.issubset(found_msgs)
        add("equipment_alerts_popped", both_popped,
            f"Expected both equipment alerts to be claimed. Found claimed: {found_msgs}")
    except Exception as e:
        add("equipment_alerts_popped", False, f"Exception: {e}")

    try:
        # medication and staffing alerts must remain unclaimed
        pending = conn.execute(
            "SELECT topic, message, claimed FROM alerts WHERE topic IN ('medication','staffing') AND claimed=0"
        ).fetchall()
        
        topics_pending = {r["topic"] for r in pending}
        med_pending = "medication" in topics_pending
        staff_pending = "staffing" in topics_pending
        
        add("non_equipment_alerts_still_pending", med_pending and staff_pending,
            f"Medication pending={med_pending}, staffing pending={staff_pending}. "
            f"Topics found: {topics_pending}")
    except Exception as e:
        add("non_equipment_alerts_still_pending", False, f"Exception: {e}")

    # ── CHECK 3: Task claimed and released ────────────────────────────────────
    try:
        row = conn.execute(
            "SELECT name, status, result, released_at FROM tasks WHERE name='night-shift-handoff-2024-01-15'"
        ).fetchone()
        if row is None:
            add("task_night_shift_exists", False, "Task night-shift-handoff-2024-01-15 not found")
        else:
            status_done = row["status"] == "done"
            result_ok = row["result"] == "night shift coordination initialized — 14 patients on census"
            released_ok = row["released_at"] is not None
            detail = (f"status={row['status']!r}, result={row['result']!r}, "
                      f"released_at={row['released_at']}")
            add("task_night_shift_correct",
                status_done and result_ok and released_ok, detail)
    except Exception as e:
        add("task_night_shift_correct", False, f"Exception: {e}")

    # ── CHECK 4: Old claimed alerts purged ────────────────────────────────────
    try:
        # The two old claimed alerts from 31h ago should have been purged
        old_alerts = conn.execute(
            "SELECT COUNT(*) as cnt FROM alerts WHERE claimed=1 AND message LIKE '%day shift handled%'"
        ).fetchone()
        count = old_alerts["cnt"] if old_alerts else None
        purged_ok = count == 0
        add("old_alerts_purged", purged_ok,
            f"Expected 0 old 'day shift handled' claimed alerts after purge, found {count}")
    except Exception as e:
        add("old_alerts_purged", False, f"Exception: {e}")

    # ── CHECK 5: shift_report.json ────────────────────────────────────────────
    try:
        report_paths = list(Path(workspace).rglob("shift_report.json"))
        if not report_paths:
            add("shift_report_exists", False, "shift_report.json not found in workspace")
        else:
            report_path = report_paths[0]
            add("shift_report_exists", True, f"Found at {report_path}")
            
            with open(report_path) as f:
                report = json.load(f)
            
            # Must have stats fields
            stats_fields = ["facts", "alerts_pending", "alerts_claimed", "tasks_claimed", "tasks_done"]
            missing = [f for f in stats_fields if f not in report]
            add("shift_report_has_stats_fields", len(missing) == 0,
                f"Missing fields: {missing}")
            
            # shift field
            shift_ok = report.get("shift") == "night"
            add("shift_report_shift_field", shift_ok,
                f"shift={report.get('shift')!r}, expected 'night'")
            
            # task_claimed field — should be True (task was successfully claimed and released)
            tc = report.get("task_claimed")
            add("shift_report_task_claimed", tc is True,
                f"task_claimed={tc!r}, expected True")
            
            # equipment_alerts_consumed — should be 2
            eac = report.get("equipment_alerts_consumed")
            add("shift_report_equipment_alerts_consumed", eac == 2,
                f"equipment_alerts_consumed={eac!r}, expected 2")
            
    except json.JSONDecodeError as e:
        add("shift_report_valid_json", False, f"Invalid JSON: {e}")
    except Exception as e:
        add("shift_report_exists", False, f"Exception reading report: {e}")

    conn.close()

    # ── Score ──────────────────────────────────────────────────────────────────
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = round(passed_checks / total_checks, 3) if total_checks > 0 else 0.0
    all_passed = all(c["passed"] for c in checks)

    return {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = main(workspace)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["passed"] else 1)