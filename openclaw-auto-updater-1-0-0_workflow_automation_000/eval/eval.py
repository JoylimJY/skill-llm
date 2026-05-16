#!/usr/bin/env python3
import sys
import json
import os
from pathlib import Path

def load_json_safe(path):
    try:
        with open(path) as f:
            return json.load(f), None
    except FileNotFoundError:
        return None, f"File not found: {path}"
    except json.JSONDecodeError as e:
        return None, f"JSON parse error in {path}: {e}"

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []
    
    log_dir = Path(workspace) / ".clawdbot" / "command_log"
    cron_db_path = log_dir / "cron_jobs.json"
    
    # ── CHECK 1: clawdbot cron add was called ─────────────────────────────────
    invocations_path = log_dir / "clawdbot_invocations.log"
    cron_add_called = False
    raw_invocations = ""
    try:
        with open(invocations_path) as f:
            raw_invocations = f.read()
        cron_add_called = "cron add" in raw_invocations
    except FileNotFoundError:
        pass
    
    checks.append({
        "name": "clawdbot_cron_add_invoked",
        "passed": cron_add_called,
        "detail": f"clawdbot cron add was {'found' if cron_add_called else 'NOT found'} in invocation log."
    })
    
    # ── CHECK 2: Cron job was registered in the DB ────────────────────────────
    jobs, err = load_json_safe(cron_db_path)
    job = None
    if err:
        checks.append({
            "name": "cron_job_registered",
            "passed": False,
            "detail": f"Could not read cron job database: {err}"
        })
    else:
        # Find the daily auto-update job
        for j in (jobs or []):
            if "auto" in j.get("name", "").lower() or "update" in j.get("name", "").lower():
                job = j
                break
        checks.append({
            "name": "cron_job_registered",
            "passed": job is not None,
            "detail": f"Daily auto-update cron job {'found' if job else 'NOT found'} in cron DB. Jobs: {jobs}"
        })
    
    # ── CHECK 3: Correct job name ─────────────────────────────────────────────
    if job:
        expected_name = "Daily Auto-Update"
        name_correct = job.get("name", "") == expected_name
        checks.append({
            "name": "correct_job_name",
            "passed": name_correct,
            "detail": f"Job name: '{job.get('name', '')}'. Expected: '{expected_name}'"
        })
    else:
        checks.append({
            "name": "correct_job_name",
            "passed": False,
            "detail": "No job found to check name."
        })
    
    # ── CHECK 4: Correct cron expression (0 4 * * *) ──────────────────────────
    if job:
        expected_cron = "0 4 * * *"
        cron_correct = job.get("cron", "").strip() == expected_cron
        checks.append({
            "name": "correct_cron_expression",
            "passed": cron_correct,
            "detail": f"Cron expr: '{job.get('cron', '')}'. Expected: '{expected_cron}'"
        })
    else:
        checks.append({
            "name": "correct_cron_expression",
            "passed": False,
            "detail": "No job found to check cron expression."
        })
    
    # ── CHECK 5: Correct timezone (America/Los_Angeles) ───────────────────────
    if job:
        expected_tz = "America/Los_Angeles"
        tz_correct = job.get("tz", "") == expected_tz
        checks.append({
            "name": "correct_timezone",
            "passed": tz_correct,
            "detail": f"Timezone: '{job.get('tz', '')}'. Expected: '{expected_tz}'"
        })
    else:
        checks.append({
            "name": "correct_timezone",
            "passed": False,
            "detail": "No job found to check timezone."
        })
    
    # ── CHECK 6: session=isolated (proprietary trap) ──────────────────────────
    if job:
        expected_session = "isolated"
        session_correct = job.get("session", "") == expected_session
        checks.append({
            "name": "correct_session_isolated",
            "passed": session_correct,
            "detail": f"Session: '{job.get('session', '')}'. Expected: '{expected_session}'. This is a proprietary flag unique to Clawdbot."
        })
    else:
        checks.append({
            "name": "correct_session_isolated",
            "passed": False,
            "detail": "No job found to check session flag."
        })
    
    # ── CHECK 7: wake=now (proprietary trap) ──────────────────────────────────
    if job:
        expected_wake = "now"
        wake_correct = job.get("wake", "") == expected_wake
        checks.append({
            "name": "correct_wake_now",
            "passed": wake_correct,
            "detail": f"Wake: '{job.get('wake', '')}'. Expected: 'now'. This --wake flag is proprietary to Clawdbot cron."
        })
    else:
        checks.append({
            "name": "correct_wake_now",
            "passed": False,
            "detail": "No job found to check wake flag."
        })
    
    # ── CHECK 8: --deliver flag set ───────────────────────────────────────────
    if job:
        deliver_set = job.get("deliver", False) is True
        checks.append({
            "name": "deliver_flag_set",
            "passed": deliver_set,
            "detail": f"Deliver flag: {job.get('deliver', False)}. Expected: True (--deliver enables push delivery of summary)."
        })
    else:
        checks.append({
            "name": "deliver_flag_set",
            "passed": False,
            "detail": "No job found to check deliver flag."
        })
    
    # ── CHECK 9: --message content references updates ─────────────────────────
    if job:
        message = job.get("message", "").lower()
        message_valid = (
            ("update" in message or "updat" in message) and
            len(message) > 10
        )
        checks.append({
            "name": "message_references_updates",
            "passed": message_valid,
            "detail": f"Message content: '{job.get('message', '')}'. Must reference update actions."
        })
    else:
        checks.append({
            "name": "message_references_updates",
            "passed": False,
            "detail": "No job found to check message content."
        })

    # ── CHECK 10: disable config JSON file exists with correct structure ──────
    # Agent should create a config file showing they understand the disable mechanism
    # Look for any JSON config with cron.enabled setting anywhere in workspace
    config_found = False
    config_detail = "No JSON file with cron.enabled configuration found in workspace."
    
    # Check the canonical .clawdbot/config.json path first
    canonical_config_path = Path(workspace) / ".clawdbot" / "config.json"
    try:
        with open(canonical_config_path) as f:
            cfg = json.load(f)
        if "cron" in cfg:
            cron_section = cfg["cron"]
            if isinstance(cron_section, dict) and "enabled" in cron_section:
                config_found = True
                config_detail = f"Found cron.enabled={cron_section['enabled']} in .clawdbot/config.json"
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        pass
    
    # Also search broadly for any config with cron.enabled
    if not config_found:
        for json_file in Path(workspace).rglob("*.json"):
            try:
                with open(json_file) as f:
                    data = json.load(f)
                if isinstance(data, dict) and "cron" in data:
                    cron_sec = data["cron"]
                    if isinstance(cron_sec, dict) and "enabled" in cron_sec:
                        config_found = True
                        config_detail = f"Found cron.enabled={cron_sec['enabled']} in {json_file}"
                        break
            except Exception:
                continue

    checks.append({
        "name": "cron_config_with_enabled_flag",
        "passed": config_found,
        "detail": config_detail
    })

    # ── Final scoring ─────────────────────────────────────────────────────────
    # Weight critical proprietary flags more heavily
    critical_checks = [
        "correct_session_isolated",   # Most proprietary
        "correct_wake_now",           # Most proprietary
        "deliver_flag_set",           # Proprietary
        "correct_cron_expression",    # Specific value
        "correct_timezone",           # Specific value
    ]
    
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    
    # Critical checks must all pass for full score
    critical_passed = all(
        next((c["passed"] for c in checks if c["name"] == name), False)
        for name in critical_checks
    )
    
    base_score = passed_count / total
    # Bonus for nailing all critical proprietary flags
    score = base_score if not critical_passed else min(1.0, base_score + 0.1)
    
    # Must pass at minimum: cron registered + at least 3 critical checks
    min_critical = sum(
        1 for name in critical_checks
        if next((c["passed"] for c in checks if c["name"] == name), False)
    )
    
    overall_passed = (
        next((c["passed"] for c in checks if c["name"] == "cron_job_registered"), False) and
        min_critical >= 3 and
        passed_count >= 6
    )
    
    result = {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()