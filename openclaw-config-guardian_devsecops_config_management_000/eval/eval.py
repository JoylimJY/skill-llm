#!/usr/bin/env python3
"""
Evaluation script for the config-guardian task.

Checks:
1. Guardian binary is installed at /usr/local/bin/openclaw-config-guardian
2. Checksum file exists and matches the binary
3. Systemd unit file exists
4. Backup directory structure is in place
5. .guardian_state.json exists and is valid JSON
6. Guardian was locked (attempts >= 3 seen in audit log) during the test
7. Guardian is currently UNLOCKED (locked == false)
8. Attempts counter is reset to 0 after unlock
9. At least one rollback event appears in the audit log
10. Baseline history directory contains at least one archived snapshot
11. Audit log contains UNLOCK event
12. Current config is valid JSON with required fields
"""

import sys
import json
import os
import subprocess
import hashlib
from pathlib import Path

def read_json(path):
    return json.loads(Path(path).read_text())

def check(name, passed, detail=""):
    return {"name": name, "passed": passed, "detail": detail}

def sha256file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

checks = []
BACKUP_DIR = Path("/root/.openclaw/backups/config")
CONFIG_PATH = Path("/root/.openclaw/openclaw.json")
GUARDIAN_BIN = Path("/usr/local/bin/openclaw-config-guardian")
CHECKSUM_FILE = BACKUP_DIR / ".guardian_checksum"
STATE_FILE = BACKUP_DIR / ".guardian_state.json"
AUDIT_LOG = BACKUP_DIR / "guardian_audit.log"
HISTORY_DIR = BACKUP_DIR / "baseline_history"
BASELINE = BACKUP_DIR / "baseline.json"
UNIT_FILE = Path("/etc/systemd/system/openclaw-config-guardian.service")

# ── Check 1: Guardian binary installed ───────────────────────────────────────
try:
    exists = GUARDIAN_BIN.exists() and os.access(GUARDIAN_BIN, os.X_OK)
    checks.append(check(
        "guardian_binary_installed",
        exists,
        f"{'Found' if exists else 'Missing'}: {GUARDIAN_BIN}"
    ))
except Exception as e:
    checks.append(check("guardian_binary_installed", False, str(e)))

# ── Check 2: Checksum file exists and is correct ──────────────────────────────
try:
    if not CHECKSUM_FILE.exists():
        checks.append(check("checksum_file_valid", False, "Checksum file missing"))
    else:
        stored = CHECKSUM_FILE.read_text().strip().split()[0]
        actual = sha256file(GUARDIAN_BIN)
        match = (stored == actual)
        checks.append(check(
            "checksum_file_valid",
            match,
            f"stored={stored[:16]}... actual={actual[:16]}... match={match}"
        ))
except Exception as e:
    checks.append(check("checksum_file_valid", False, str(e)))

# ── Check 3: Systemd unit exists ──────────────────────────────────────────────
try:
    unit_exists = UNIT_FILE.exists()
    checks.append(check(
        "systemd_unit_exists",
        unit_exists,
        f"{'Found' if unit_exists else 'Missing'}: {UNIT_FILE}"
    ))
except Exception as e:
    checks.append(check("systemd_unit_exists", False, str(e)))

# ── Check 4: Backup directory structure ───────────────────────────────────────
try:
    dirs_ok = BACKUP_DIR.is_dir() and HISTORY_DIR.is_dir()
    checks.append(check(
        "backup_directory_structure",
        dirs_ok,
        f"backup_dir={BACKUP_DIR.is_dir()} history_dir={HISTORY_DIR.is_dir()}"
    ))
except Exception as e:
    checks.append(check("backup_directory_structure", False, str(e)))

# ── Check 5: State file is valid JSON ─────────────────────────────────────────
try:
    if not STATE_FILE.exists():
        checks.append(check("state_file_valid_json", False, "State file missing"))
        state = None
    else:
        state = read_json(STATE_FILE)
        checks.append(check("state_file_valid_json", True, f"keys={list(state.keys())}"))
except Exception as e:
    checks.append(check("state_file_valid_json", False, str(e)))
    state = None

# ── Check 6: State shows currently UNLOCKED ───────────────────────────────────
try:
    if state is None:
        checks.append(check("state_is_unlocked", False, "State could not be read"))
    else:
        locked = state.get("locked", None)
        is_unlocked = (locked is False or locked == "false")
        checks.append(check(
            "state_is_unlocked",
            is_unlocked,
            f"locked={locked!r} (expected false)"
        ))
except Exception as e:
    checks.append(check("state_is_unlocked", False, str(e)))

# ── Check 7: Attempts counter reset to 0 ─────────────────────────────────────
try:
    if state is None:
        checks.append(check("attempts_reset_to_zero", False, "State not readable"))
    else:
        attempts = state.get("attempts", -1)
        ok = (attempts == 0)
        checks.append(check(
            "attempts_reset_to_zero",
            ok,
            f"attempts={attempts} (expected 0)"
        ))
except Exception as e:
    checks.append(check("attempts_reset_to_zero", False, str(e)))

# ── Check 8: Audit log has ROLLBACK events ────────────────────────────────────
try:
    if not AUDIT_LOG.exists():
        checks.append(check("audit_log_has_rollback", False, "Audit log missing"))
    else:
        lines = AUDIT_LOG.read_text().strip().splitlines()
        events = []
        for line in lines:
            try:
                obj = json.loads(line)
                events.append(obj.get("event", ""))
            except Exception:
                pass
        has_rollback = any("ROLLBACK" in e for e in events)
        checks.append(check(
            "audit_log_has_rollback",
            has_rollback,
            f"events found: {list(set(events))}"
        ))
except Exception as e:
    checks.append(check("audit_log_has_rollback", False, str(e)))

# ── Check 9: Audit log has LOCKED event ──────────────────────────────────────
try:
    if not AUDIT_LOG.exists():
        checks.append(check("audit_log_has_locked_event", False, "Audit log missing"))
    else:
        lines = AUDIT_LOG.read_text().strip().splitlines()
        events = []
        for line in lines:
            try:
                obj = json.loads(line)
                events.append(obj.get("event", ""))
            except Exception:
                pass
        has_locked = "LOCKED" in events
        checks.append(check(
            "audit_log_has_locked_event",
            has_locked,
            f"All events: {events}"
        ))
except Exception as e:
    checks.append(check("audit_log_has_locked_event", False, str(e)))

# ── Check 10: Audit log has UNLOCK event ─────────────────────────────────────
try:
    if not AUDIT_LOG.exists():
        checks.append(check("audit_log_has_unlock_event", False, "Audit log missing"))
    else:
        lines = AUDIT_LOG.read_text().strip().splitlines()
        events = []
        for line in lines:
            try:
                obj = json.loads(line)
                events.append(obj.get("event", ""))
            except Exception:
                pass
        has_unlock = "UNLOCK" in events
        checks.append(check(
            "audit_log_has_unlock_event",
            has_unlock,
            f"All events: {events}"
        ))
except Exception as e:
    checks.append(check("audit_log_has_unlock_event", False, str(e)))

# ── Check 11: Baseline history has at least one archived snapshot ─────────────
try:
    if not HISTORY_DIR.exists():
        checks.append(check("baseline_history_has_snapshots", False, "History dir missing"))
    else:
        snapshots = list(HISTORY_DIR.glob("baseline_*.json"))
        ok = len(snapshots) >= 1
        checks.append(check(
            "baseline_history_has_snapshots",
            ok,
            f"Found {len(snapshots)} snapshots: {[s.name for s in snapshots[:5]]}"
        ))
except Exception as e:
    checks.append(check("baseline_history_has_snapshots", False, str(e)))

# ── Check 12: Current config.json is valid and has required fields ────────────
try:
    if not CONFIG_PATH.exists():
        checks.append(check("current_config_valid", False, "Config file missing"))
    else:
        cfg = read_json(CONFIG_PATH)
        has_fields = all(k in cfg for k in ("gateway_id", "port", "environment"))
        checks.append(check(
            "current_config_valid",
            has_fields,
            f"keys={list(cfg.keys())} required=(gateway_id, port, environment)"
        ))
except Exception as e:
    checks.append(check("current_config_valid", False, str(e)))

# ── Check 13: Baseline exists ────────────────────────────────────────────────
try:
    bl_exists = BASELINE.exists()
    checks.append(check(
        "baseline_file_exists",
        bl_exists,
        f"{'Found' if bl_exists else 'Missing'}: {BASELINE}"
    ))
except Exception as e:
    checks.append(check("baseline_file_exists", False, str(e)))

# ── Score ─────────────────────────────────────────────────────────────────────
passed_count = sum(1 for c in checks if c["passed"])
total = len(checks)
score = round(passed_count / total, 4)
all_passed = (passed_count == total)

result = {
    "passed": all_passed,
    "score": score,
    "checks": checks
}

print(json.dumps(result, indent=2))
sys.exit(0 if all_passed else 1)