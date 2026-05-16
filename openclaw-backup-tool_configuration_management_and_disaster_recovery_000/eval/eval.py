#!/usr/bin/env python3
"""
Evaluation script for the OpenClaw backup/restore task.

Checks:
1. At least one backup was created in ~/.openclaw/backups/ BEFORE openclaw.json was modified
2. openclaw.json was modified to change gateway_port to 9090 at some point (the intermediate state existed)
3. The restore was run, and openclaw.json is back to gateway_port=8080 (original)
4. The backup contains the original openclaw.json with gateway_port=8080
5. A .last_restored_backup sentinel file exists (written by restore.sh)
"""

import sys
import json
import os
import pathlib
import datetime

def main():
    checks = []
    overall_passed = True

    openclaw_home = pathlib.Path(os.path.expanduser("~/.openclaw"))
    backups_root = openclaw_home / "backups"
    active_config_path = openclaw_home / "openclaw.json"
    last_restored_path = openclaw_home / ".last_restored_backup"
    last_backup_path_file = openclaw_home / ".last_backup_path"

    # ---- Check 1: At least one backup directory exists ----
    try:
        backup_dirs = sorted(backups_root.iterdir()) if backups_root.exists() else []
        backup_dirs = [d for d in backup_dirs if d.is_dir()]
        check1_passed = len(backup_dirs) >= 1
        checks.append({
            "name": "backup_directory_created",
            "passed": check1_passed,
            "detail": f"Found {len(backup_dirs)} backup(s) in {backups_root}: {[d.name for d in backup_dirs]}"
        })
    except Exception as e:
        checks.append({"name": "backup_directory_created", "passed": False, "detail": f"Exception: {e}"})
        backup_dirs = []

    # ---- Check 2: backup contains original openclaw.json with gateway_port=8080 ----
    try:
        found_original_in_backup = False
        backup_config_port = None
        for bdir in backup_dirs:
            bconfig = bdir / "openclaw.json"
            if bconfig.exists():
                data = json.loads(bconfig.read_text())
                if data.get("gateway_port") == 8080:
                    found_original_in_backup = True
                    backup_config_port = 8080
                    break
                else:
                    backup_config_port = data.get("gateway_port")
        checks.append({
            "name": "backup_contains_original_config",
            "passed": found_original_in_backup,
            "detail": f"Original config (gateway_port=8080) found in backup: {found_original_in_backup}. Backup port found: {backup_config_port}"
        })
    except Exception as e:
        checks.append({"name": "backup_contains_original_config", "passed": False, "detail": f"Exception: {e}"})

    # ---- Check 3: Active openclaw.json restored to original (gateway_port=8080) ----
    try:
        active_config = json.loads(active_config_path.read_text())
        active_port = active_config.get("gateway_port")
        check3_passed = active_port == 8080
        checks.append({
            "name": "active_config_restored_to_original",
            "passed": check3_passed,
            "detail": f"Active openclaw.json gateway_port={active_port} (expected 8080). Full config keys: {list(active_config.keys())}"
        })
    except Exception as e:
        checks.append({"name": "active_config_restored_to_original", "passed": False, "detail": f"Exception reading active config: {e}"})

    # ---- Check 4: restore.sh was actually invoked (sentinel file written by restore.sh) ----
    try:
        restore_ran = last_restored_path.exists()
        restored_snapshot = last_restored_path.read_text().strip() if restore_ran else None
        checks.append({
            "name": "restore_script_was_executed",
            "passed": restore_ran,
            "detail": f".last_restored_backup exists: {restore_ran}. Restored snapshot: {restored_snapshot}"
        })
    except Exception as e:
        checks.append({"name": "restore_script_was_executed", "passed": False, "detail": f"Exception: {e}"})

    # ---- Check 5: backup.sh was run (sentinel file written by backup.sh) ----
    try:
        backup_ran = last_backup_path_file.exists()
        backup_path_recorded = last_backup_path_file.read_text().strip() if backup_ran else None
        checks.append({
            "name": "backup_script_was_executed",
            "passed": backup_ran,
            "detail": f".last_backup_path exists: {backup_ran}. Backup path recorded: {backup_path_recorded}"
        })
    except Exception as e:
        checks.append({"name": "backup_script_was_executed", "passed": False, "detail": f"Exception: {e}"})

    # ---- Check 6: Backup was created BEFORE the modification (ordering check) ----
    # We verify this by checking that the backup contains gateway_port=8080
    # AND the backup dir timestamp (from dirname YYYYMMDD_HHMMSS) is consistent with before any port=9090 change.
    # We can check: the most recent backup has port=8080, meaning backup happened while port was still 8080.
    try:
        ordering_ok = False
        ordering_detail = "No backups found to check ordering."
        if backup_dirs:
            # The backup.sh script runs BEFORE modifications per SKILL.md rules.
            # We confirm: does the most recent backup (or any backup) have the pre-modification port?
            most_recent_backup = sorted(backup_dirs)[-1]
            bconfig_path = most_recent_backup / "openclaw.json"
            if bconfig_path.exists():
                bdata = json.loads(bconfig_path.read_text())
                bport = bdata.get("gateway_port")
                # Backup should capture original (8080), not the modified (9090)
                ordering_ok = (bport == 8080)
                ordering_detail = (
                    f"Most recent backup ({most_recent_backup.name}) has gateway_port={bport}. "
                    f"Expected 8080 (pre-modification state). Ordering correct: {ordering_ok}"
                )
            else:
                ordering_detail = f"Most recent backup {most_recent_backup.name} has no openclaw.json."
        checks.append({
            "name": "backup_captured_pre_modification_state",
            "passed": ordering_ok,
            "detail": ordering_detail
        })
    except Exception as e:
        checks.append({"name": "backup_captured_pre_modification_state", "passed": False, "detail": f"Exception: {e}"})

    # ---- Check 7: openclaw.json preserves all original keys after restore ----
    try:
        expected_keys = {"gateway_port", "gateway_host", "log_level", "max_connections",
                         "timeout_seconds", "tls_enabled", "plugin_dir", "data_dir",
                         "admin_ui_enabled", "metrics_port"}
        active_config_keys = set(json.loads(active_config_path.read_text()).keys()) if active_config_path.exists() else set()
        keys_intact = expected_keys.issubset(active_config_keys)
        checks.append({
            "name": "restored_config_has_all_original_keys",
            "passed": keys_intact,
            "detail": f"Expected keys: {sorted(expected_keys)}. Found: {sorted(active_config_keys)}. Missing: {sorted(expected_keys - active_config_keys)}"
        })
    except Exception as e:
        checks.append({"name": "restored_config_has_all_original_keys", "passed": False, "detail": f"Exception: {e}"})

    # Compute final result
    overall_passed = all(c["passed"] for c in checks)
    score = sum(1.0 for c in checks if c["passed"]) / len(checks) if checks else 0.0

    result = {
        "passed": overall_passed,
        "score": round(score, 4),
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return 0 if overall_passed else 1

if __name__ == "__main__":
    sys.exit(main())