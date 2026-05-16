#!/usr/bin/env python3
"""
Evaluation script for the automation-scripts skill task.
Usage: python3 eval_script.py /workspace
"""
import sys
import json
import os
from pathlib import Path

def load_json_file(path):
    return json.loads(Path(path).read_text())

def run_checks(workspace_str):
    workspace = Path(workspace_str)
    scripts_dir = workspace / "scripts"
    custom_dir = scripts_dir / "custom"
    logs_dir = scripts_dir / "logs"
    config_path = scripts_dir / "config.conf"
    schedule_path = scripts_dir / ".schedules.json"
    status_path = scripts_dir / ".status.json"

    checks = []
    total_score = 0.0
    max_score = 6.0

    # ── CHECK 1: A backup-prefixed script was created ─────────────────────────
    check_name = "backup_script_created_with_correct_prefix"
    try:
        backup_scripts = list(custom_dir.glob("backup-*.sh"))
        if backup_scripts:
            checks.append({
                "name": check_name,
                "passed": True,
                "detail": f"Found backup script(s): {[s.name for s in backup_scripts]}"
            })
            total_score += 1.0
        else:
            checks.append({
                "name": check_name,
                "passed": False,
                "detail": f"No script with 'backup-' prefix found in {custom_dir}. Found: {[s.name for s in custom_dir.glob('*.sh')]}"
            })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # Identify the backup script name for subsequent checks
    backup_script_name = None
    try:
        backup_scripts = list(custom_dir.glob("backup-*.sh"))
        if backup_scripts:
            backup_script_name = backup_scripts[0].stem
    except Exception:
        pass

    # ── CHECK 2: config.conf has canonical correct values ─────────────────────
    check_name = "config_conf_has_canonical_values"
    try:
        cfg = load_json_file(config_path)
        auto = cfg.get("automation", {})
        notif = auto.get("notifications", {})
        issues = []
        if auto.get("enabled") is not True:
            issues.append(f"enabled={auto.get('enabled')} (expected true)")
        if auto.get("logRetentionDays") != 30:
            issues.append(f"logRetentionDays={auto.get('logRetentionDays')} (expected 30)")
        if auto.get("maxRetries") != 3:
            issues.append(f"maxRetries={auto.get('maxRetries')} (expected 3)")
        if auto.get("retryDelay") != 60:
            issues.append(f"retryDelay={auto.get('retryDelay')} (expected 60)")
        if notif.get("onFailure") is not True:
            issues.append(f"notifications.onFailure={notif.get('onFailure')} (expected true)")
        if notif.get("onSuccess") is not False:
            issues.append(f"notifications.onSuccess={notif.get('onSuccess')} (expected false)")
        if not issues:
            checks.append({"name": check_name, "passed": True, "detail": "config.conf has all correct canonical values"})
            total_score += 1.0
        else:
            checks.append({"name": check_name, "passed": False, "detail": "Config issues: " + "; ".join(issues)})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception reading config: {e}"})

    # ── CHECK 3: Script is registered with enabled=True in .status.json ───────
    check_name = "script_registered_and_enabled"
    try:
        if backup_script_name is None:
            checks.append({"name": check_name, "passed": False, "detail": "No backup script found to check status for"})
        else:
            status = load_json_file(status_path)
            entry = status.get(backup_script_name)
            if entry is None:
                checks.append({"name": check_name, "passed": False, "detail": f"'{backup_script_name}' not found in .status.json"})
            elif entry.get("enabled") is True:
                checks.append({"name": check_name, "passed": True, "detail": f"'{backup_script_name}' is registered and enabled"})
                total_score += 1.0
            else:
                checks.append({"name": check_name, "passed": False, "detail": f"'{backup_script_name}' exists but enabled={entry.get('enabled')}"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ── CHECK 4: Script is scheduled with a valid nightly cron expression ─────
    check_name = "script_scheduled_with_nightly_cron"
    try:
        if backup_script_name is None:
            checks.append({"name": check_name, "passed": False, "detail": "No backup script found to check schedule for"})
        else:
            schedules = load_json_file(schedule_path)
            sched_entry = schedules.get(backup_script_name)
            if sched_entry is None:
                checks.append({"name": check_name, "passed": False, "detail": f"'{backup_script_name}' has no schedule in .schedules.json"})
            else:
                cron = sched_entry.get("cron", "")
                parts = cron.strip().split()
                if len(parts) != 5:
                    checks.append({"name": check_name, "passed": False, "detail": f"Cron '{cron}' does not have 5 fields"})
                else:
                    # Nightly: must run once per day or at a nightly hour (typically 0-6 or 22-23)
                    # Must not be peak hours (9-17 business hours) - per SKILL.md best practice
                    hour_field = parts[1]
                    # Accept specific hours (integer) or ranges that are off-peak
                    peak_hours = set(range(9, 18))
                    try:
                        hour_val = int(hour_field)
                        is_off_peak = hour_val not in peak_hours
                    except ValueError:
                        # If it's a wildcard or range, check if it avoids peak hours
                        is_off_peak = (hour_field == "*")  # wildcard is ambiguous, be strict
                        is_off_peak = False  # non-integer non-wildcard: strict reject unless valid
                        if hour_field == "*":
                            is_off_peak = False  # running every hour is not "nightly"
                    
                    # Also check: minute field, day fields should indicate daily run
                    minute_field = parts[0]
                    dom_field = parts[2]
                    month_field = parts[3]
                    dow_field = parts[4]
                    is_daily = (dom_field == "*" and month_field == "*")
                    
                    passed = is_off_peak and is_daily
                    checks.append({
                        "name": check_name,
                        "passed": passed,
                        "detail": f"Cron='{cron}', off_peak={is_off_peak}, daily={is_daily}"
                    })
                    if passed:
                        total_score += 1.0
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ── CHECK 5: Script was executed and a log entry exists ───────────────────
    check_name = "script_executed_with_log_entry"
    try:
        if backup_script_name is None:
            checks.append({"name": check_name, "passed": False, "detail": "No backup script found to check log for"})
        else:
            log_path = logs_dir / f"{backup_script_name}.log"
            if not log_path.exists():
                checks.append({"name": check_name, "passed": False, "detail": f"No log file found at {log_path}"})
            else:
                entries = json.loads(log_path.read_text())
                if not isinstance(entries, list) or len(entries) == 0:
                    checks.append({"name": check_name, "passed": False, "detail": "Log file exists but has no entries"})
                else:
                    checks.append({"name": check_name, "passed": True, "detail": f"Log has {len(entries)} entry/entries"})
                    total_score += 1.0
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ── CHECK 6: Log entry has all required fields per SKILL.md ───────────────
    check_name = "log_entry_has_all_required_fields"
    REQUIRED_LOG_FIELDS = {"timestamp", "script", "status", "duration", "output", "error"}
    try:
        if backup_script_name is None:
            checks.append({"name": check_name, "passed": False, "detail": "No backup script found"})
        else:
            log_path = logs_dir / f"{backup_script_name}.log"
            entries = json.loads(log_path.read_text())
            last_entry = entries[-1]
            present = set(last_entry.keys())
            missing = REQUIRED_LOG_FIELDS - present
            if not missing:
                status_val = last_entry.get("status", "")
                if status_val in ("success", "failure"):
                    checks.append({
                        "name": check_name,
                        "passed": True,
                        "detail": f"All required fields present. status='{status_val}'"
                    })
                    total_score += 1.0
                else:
                    checks.append({
                        "name": check_name,
                        "passed": False,
                        "detail": f"status field value '{status_val}' is not 'success' or 'failure'"
                    })
            else:
                checks.append({
                    "name": check_name,
                    "passed": False,
                    "detail": f"Missing log fields: {missing}"
                })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    passed_all = all(c["passed"] for c in checks)
    score = round(total_score / max_score, 4)

    result = {
        "passed": passed_all,
        "score": score,
        "checks": checks
    }
    return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    result = run_checks(sys.argv[1])
    print(json.dumps(result, indent=2))