#!/usr/bin/env python3
"""
Evaluation script for neckr0ik-session-healer task.

Checks:
  1. Stale lock 1 was cleared (STALE_SESSION_1 → dead PID 99991)
  2. Stale lock 2 was cleared (STALE_SESSION_2 → dead PID 99992)
  3. Active lock is still present (ACTIVE_SESSION → alive PID 1)
  4. Corrupted session 2 JSONL was recovered (all remaining lines are valid JSON)
  5. Backup was created for session 2 before recovery
  6. Backup itself contains the original corrupted content
  7. Audit log exists and records heal/recover actions
"""

import sys
import json
import os
from pathlib import Path

def run_checks(workspace: str):
    home = Path("/root")
    agents_root = home / ".openclaw" / "agents"

    STALE_SESSION_1 = "c4fa26e6-20be-4843-9678-a2f328dd1844"
    STALE_SESSION_2 = "7e3b9a12-ff01-4c88-bde0-98765dcba210"
    ACTIVE_SESSION  = "a1b2c3d4-5678-90ab-cdef-1234567890ab"

    checks = []

    # ── Check 1: Stale lock 1 is gone ───────────────────────────────────────
    lock1 = agents_root / "main" / "sessions" / STALE_SESSION_1 / f"{STALE_SESSION_1}.jsonl.lock"
    try:
        exists = lock1.exists()
        checks.append({
            "name": "stale_lock_1_cleared",
            "passed": not exists,
            "detail": f"Lock file {'still exists' if exists else 'was correctly removed'}: {lock1}"
        })
    except Exception as e:
        checks.append({"name": "stale_lock_1_cleared", "passed": False, "detail": f"Exception: {e}"})

    # ── Check 2: Stale lock 2 is gone ───────────────────────────────────────
    lock2 = agents_root / "helpdesk" / "sessions" / STALE_SESSION_2 / f"{STALE_SESSION_2}.jsonl.lock"
    try:
        exists = lock2.exists()
        checks.append({
            "name": "stale_lock_2_cleared",
            "passed": not exists,
            "detail": f"Lock file {'still exists' if exists else 'was correctly removed'}: {lock2}"
        })
    except Exception as e:
        checks.append({"name": "stale_lock_2_cleared", "passed": False, "detail": f"Exception: {e}"})

    # ── Check 3: Active lock is untouched ────────────────────────────────────
    lock3 = agents_root / "main" / "sessions" / ACTIVE_SESSION / f"{ACTIVE_SESSION}.jsonl.lock"
    try:
        exists = lock3.exists()
        if exists:
            data = json.loads(lock3.read_text())
            pid_ok = data.get("pid") == 1
        else:
            pid_ok = False
        checks.append({
            "name": "active_lock_preserved",
            "passed": exists and pid_ok,
            "detail": f"Active lock {'exists with correct PID=1' if (exists and pid_ok) else 'was incorrectly removed or modified'}"
        })
    except Exception as e:
        checks.append({"name": "active_lock_preserved", "passed": False, "detail": f"Exception: {e}"})

    # ── Check 4: Recovered JSONL contains only valid JSON lines ───────────────
    jsonl2 = agents_root / "helpdesk" / "sessions" / STALE_SESSION_2 / f"{STALE_SESSION_2}.jsonl"
    try:
        if not jsonl2.exists():
            checks.append({"name": "session2_jsonl_recovered", "passed": False,
                           "detail": f"Session JSONL file missing: {jsonl2}"})
        else:
            lines = jsonl2.read_text().strip().splitlines()
            valid_lines = []
            invalid_lines = []
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    json.loads(line)
                    valid_lines.append(line)
                except json.JSONDecodeError:
                    invalid_lines.append(line)
            all_valid = len(invalid_lines) == 0 and len(valid_lines) >= 1
            checks.append({
                "name": "session2_jsonl_recovered",
                "passed": all_valid,
                "detail": (f"JSONL has {len(valid_lines)} valid lines and {len(invalid_lines)} invalid lines. "
                           f"{'All corrupted lines removed.' if all_valid else 'Corrupted lines remain!'}")
            })
    except Exception as e:
        checks.append({"name": "session2_jsonl_recovered", "passed": False, "detail": f"Exception: {e}"})

    # ── Check 5: Backup file exists for session 2 ─────────────────────────────
    backup2 = agents_root / "helpdesk" / "sessions" / STALE_SESSION_2 / f"{STALE_SESSION_2}.jsonl.bak"
    try:
        exists = backup2.exists()
        checks.append({
            "name": "session2_backup_created",
            "passed": exists,
            "detail": f"Backup file {'exists' if exists else 'MISSING'}: {backup2}"
        })
    except Exception as e:
        checks.append({"name": "session2_backup_created", "passed": False, "detail": f"Exception: {e}"})

    # ── Check 6: Backup contains original corrupted content ───────────────────
    try:
        if not backup2.exists():
            checks.append({"name": "backup_contains_original_data", "passed": False,
                           "detail": "Backup file does not exist, cannot verify content."})
        else:
            bak_content = backup2.read_bytes()
            # The original file had corrupted lines with null bytes or broken JSON
            # At minimum, the backup should have MORE content than the recovered file
            # and should contain at least one line that is NOT valid JSON
            bak_lines = bak_content.decode("utf-8", errors="replace").strip().splitlines()
            bak_invalid = 0
            for line in bak_lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    json.loads(line)
                except json.JSONDecodeError:
                    bak_invalid += 1
            has_corruption = bak_invalid > 0
            checks.append({
                "name": "backup_contains_original_data",
                "passed": has_corruption,
                "detail": (f"Backup has {len(bak_lines)} lines, {bak_invalid} are invalid JSON "
                           f"({'confirms original corrupt data preserved' if has_corruption else 'backup seems clean - may not be original'})")
            })
    except Exception as e:
        checks.append({"name": "backup_contains_original_data", "passed": False, "detail": f"Exception: {e}"})

    # ── Check 7: Audit log records actions ────────────────────────────────────
    audit_log = home / ".openclaw" / "healer-audit.log"
    try:
        if not audit_log.exists():
            checks.append({"name": "audit_log_exists", "passed": False,
                           "detail": f"Audit log not found at {audit_log}"})
        else:
            content = audit_log.read_text()
            has_cleared = "CLEARED" in content
            has_recovered = "RECOVERED" in content
            has_backup = "BACKUP" in content
            all_present = has_cleared and has_recovered and has_backup
            checks.append({
                "name": "audit_log_exists",
                "passed": all_present,
                "detail": (f"Audit log entries: CLEARED={'yes' if has_cleared else 'NO'}, "
                           f"BACKUP={'yes' if has_backup else 'NO'}, "
                           f"RECOVERED={'yes' if has_recovered else 'NO'}")
            })
    except Exception as e:
        checks.append({"name": "audit_log_exists", "passed": False, "detail": f"Exception: {e}"})

    # ── Compute score ─────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = passed_count / total if total > 0 else 0.0
    all_passed = all(c["passed"] for c in checks)

    return {
        "passed": all_passed,
        "score": round(score, 4),
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace)
    print(json.dumps(result, indent=2))