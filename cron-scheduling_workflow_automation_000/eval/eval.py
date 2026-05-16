import sys
import os
import json
import re
from pathlib import Path

def load_file(path):
    try:
        with open(path, "r") as f:
            return f.read()
    except Exception as e:
        return None

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace):
    checks = []

    # ─── FIND REQUIRED FILES ──────────────────────────────────────────────────

    # 1. pipeline.crontab
    crontab_candidates = list(Path(workspace).rglob("pipeline.crontab"))
    crontab_path = str(crontab_candidates[0]) if crontab_candidates else None
    crontab = load_file(crontab_path) if crontab_path else None

    # 2. archive.service
    service_candidates = list(Path(workspace).rglob("archive.service"))
    service_path = str(service_candidates[0]) if service_candidates else None
    service = load_file(service_path) if service_path else None

    # 3. archive.timer
    timer_candidates = list(Path(workspace).rglob("archive.timer"))
    timer_path = str(timer_candidates[0]) if timer_candidates else None
    timer = load_file(timer_path) if timer_path else None

    # 4. job_wrapper.sh (must be replaced/updated in scripts/)
    wrapper_path = os.path.join(workspace, "scripts", "job_wrapper.sh")
    wrapper = load_file(wrapper_path)

    # ═══════════════════════════════════════════════════════════════
    # CRONTAB CHECKS
    # ═══════════════════════════════════════════════════════════════

    # Check: crontab file exists
    checks.append(check(
        "crontab_file_exists",
        crontab is not None,
        f"Found at: {crontab_path}" if crontab_path else "pipeline.crontab not found anywhere in workspace"
    ))

    if crontab:
        lines = [l.strip() for l in crontab.splitlines()]
        non_blank = [l for l in lines if l and not l.startswith("#")]

        # Check: PATH is set
        path_lines = [l for l in non_blank if l.startswith("PATH=")]
        checks.append(check(
            "crontab_has_PATH",
            len(path_lines) > 0,
            f"PATH line: {path_lines[0] if path_lines else 'MISSING'}"
        ))

        # Check: MAILTO is set
        mailto_lines = [l for l in non_blank if l.startswith("MAILTO=")]
        checks.append(check(
            "crontab_has_MAILTO",
            len(mailto_lines) > 0,
            f"MAILTO line: {mailto_lines[0] if mailto_lines else 'MISSING'}"
        ))

        # Check: SHELL is set
        shell_lines = [l for l in non_blank if l.startswith("SHELL=")]
        checks.append(check(
            "crontab_has_SHELL",
            len(shell_lines) > 0,
            f"SHELL line: {shell_lines[0] if shell_lines else 'MISSING'}"
        ))

        # Check: TZ=UTC is set (DST-safe requirement)
        tz_lines = [l for l in non_blank if re.match(r"TZ\s*=\s*UTC", l)]
        checks.append(check(
            "crontab_has_TZ_UTC",
            len(tz_lines) > 0,
            f"TZ line: {tz_lines[0] if tz_lines else 'MISSING - DST-safe scheduling requires TZ=UTC'}"
        ))

        # Check: 15-min business hours ingest job (Mon-Fri, 9-17)
        # Expected pattern: */15 9-17 * * 1-5 ... ingest.sh (with flock)
        ingest_lines = [l for l in lines if "ingest.sh" in l and not l.startswith("#")]
        ingest_ok = False
        ingest_detail = "No ingest.sh cron line found"
        for il in ingest_lines:
            # Check */15 in minute field, 9-17 in hour field, 1-5 in dow field
            parts = il.split()
            if len(parts) >= 6:
                minute_ok = parts[0] == "*/15"
                hour_ok = parts[1] == "9-17"
                dom_ok = parts[2] == "*"
                month_ok = parts[3] == "*"
                dow_ok = parts[4] == "1-5"
                if minute_ok and hour_ok and dom_ok and month_ok and dow_ok:
                    ingest_ok = True
                    ingest_detail = f"Correct schedule: {il}"
                else:
                    ingest_detail = f"Wrong fields: {il} (need */15 9-17 * * 1-5)"
        # Also allow flock usage on that line (bonus but required per skill)
        checks.append(check(
            "crontab_ingest_schedule_correct",
            ingest_ok,
            ingest_detail
        ))

        # Check: ingest job uses flock to prevent overlap
        ingest_flock_ok = False
        for il in ingest_lines:
            if "flock" in il:
                ingest_flock_ok = True
        checks.append(check(
            "crontab_ingest_uses_flock",
            ingest_flock_ok,
            "flock found in ingest cron line" if ingest_flock_ok else "flock NOT found - overlapping runs not prevented"
        ))

        # Check: daily report job at 6:30 AM UTC on weekdays
        report_lines = [l for l in lines if "daily_report.sh" in l and not l.startswith("#")]
        report_ok = False
        report_detail = "No daily_report.sh cron line found"
        for rl in report_lines:
            parts = rl.split()
            if len(parts) >= 6:
                minute_ok = parts[0] == "30"
                hour_ok = parts[1] == "6"
                dom_ok = parts[2] == "*"
                month_ok = parts[3] == "*"
                dow_ok = parts[4] in ("1-5", "Mon-Fri")
                if minute_ok and hour_ok and dom_ok and month_ok and dow_ok:
                    report_ok = True
                    report_detail = f"Correct: {rl}"
                else:
                    report_detail = f"Wrong: {rl} (need 30 6 * * 1-5)"
        checks.append(check(
            "crontab_daily_report_schedule_correct",
            report_ok,
            report_detail
        ))

        # Check: quarterly cleanup job on 1st of Jan/Apr/Jul/Oct at midnight
        # Expected: 0 0 1 1,4,7,10 * /workspace/scripts/quarterly_cleanup.sh
        quarterly_lines = [l for l in lines if "quarterly_cleanup.sh" in l and not l.startswith("#")]
        quarterly_ok = False
        quarterly_detail = "No quarterly_cleanup.sh cron line found"
        for ql in quarterly_lines:
            parts = ql.split()
            if len(parts) >= 6:
                minute_ok = parts[0] == "0"
                hour_ok = parts[1] == "0"
                dom_ok = parts[2] == "1"
                # Month field must contain 1,4,7,10 (possibly in any order)
                month_field = parts[3]
                month_nums = set(re.split(r"[,]", month_field))
                month_ok = month_nums == {"1", "4", "7", "10"}
                dow_ok = parts[4] == "*"
                if minute_ok and hour_ok and dom_ok and month_ok and dow_ok:
                    quarterly_ok = True
                    quarterly_detail = f"Correct: {ql}"
                else:
                    quarterly_detail = f"Wrong: {ql} (need 0 0 1 1,4,7,10 *)"
        checks.append(check(
            "crontab_quarterly_cleanup_correct",
            quarterly_ok,
            quarterly_detail
        ))

        # Check: @reboot preflight job
        reboot_lines = [l for l in lines if "@reboot" in l and "preflight.sh" in l and not l.startswith("#")]
        checks.append(check(
            "crontab_reboot_preflight",
            len(reboot_lines) > 0,
            f"@reboot preflight line: {reboot_lines[0] if reboot_lines else 'MISSING'}"
        ))

        # Check: no critical jobs scheduled between 1-3 AM (DST danger zone)
        # Scan all cron job lines (not @reboot, not env vars) for hour in 1-2
        dst_danger = False
        dst_danger_detail = "No jobs in DST danger zone (1-3 AM)"
        for l in lines:
            if l.startswith("#") or "=" in l.split()[0] if l.split() else True:
                continue
            parts = l.split()
            if len(parts) >= 5 and not l.startswith("@"):
                hour_field = parts[1]
                # Check if hour field is a single number in 1 or 2
                if hour_field in ("1", "2"):
                    dst_danger = True
                    dst_danger_detail = f"Job scheduled in DST danger zone: {l}"
        checks.append(check(
            "crontab_no_DST_danger_zone_jobs",
            not dst_danger,
            dst_danger_detail
        ))

        # Check: output redirected to log (>> ... 2>&1) on job lines
        job_lines = [l for l in lines if l and not l.startswith("#") and "=" not in (l.split()[0] if l.split() else "=")]
        # Filter out @-style without commands or env lines
        cron_job_lines = []
        for l in job_lines:
            parts = l.split()
            if not parts:
                continue
            if parts[0].startswith("@") or (len(parts) > 0 and re.match(r"^[\*/0-9,\-]+$", parts[0])):
                cron_job_lines.append(l)

        redirect_ok = all(">>" in l and "2>&1" in l for l in cron_job_lines) if cron_job_lines else False
        missing_redirect = [l for l in cron_job_lines if ">>" not in l or "2>&1" not in l]
        checks.append(check(
            "crontab_output_redirected",
            redirect_ok,
            "All job lines redirect output" if redirect_ok else f"Missing redirection on: {missing_redirect[:2]}"
        ))

    else:
        # Add failing checks for all crontab sub-checks
        for name in [
            "crontab_has_PATH", "crontab_has_MAILTO", "crontab_has_SHELL",
            "crontab_has_TZ_UTC", "crontab_ingest_schedule_correct",
            "crontab_ingest_uses_flock", "crontab_daily_report_schedule_correct",
            "crontab_quarterly_cleanup_correct", "crontab_reboot_preflight",
            "crontab_no_DST_danger_zone_jobs", "crontab_output_redirected"
        ]:
            checks.append(check(name, False, "pipeline.crontab not found"))

    # ═══════════════════════════════════════════════════════════════
    # SYSTEMD SERVICE CHECKS
    # ═══════════════════════════════════════════════════════════════

    checks.append(check(
        "service_file_exists",
        service is not None,
        f"Found at: {service_path}" if service_path else "archive.service not found"
    ))

    if service:
        # Check: [Unit] section
        has_unit = "[Unit]" in service
        checks.append(check("service_has_Unit_section", has_unit, "[Unit] section present" if has_unit else "Missing [Unit]"))

        # Check: [Service] section
        has_service_section = "[Service]" in service
        checks.append(check("service_has_Service_section", has_service_section, "[Service] section present" if has_service_section else "Missing [Service]"))

        # Check: Type=oneshot
        has_oneshot = bool(re.search(r"Type\s*=\s*oneshot", service))
        checks.append(check("service_Type_oneshot", has_oneshot, "Type=oneshot present" if has_oneshot else "Missing Type=oneshot"))

        # Check: ExecStart points to archive.sh
        has_execstart = bool(re.search(r"ExecStart\s*=.*archive\.sh", service))
        checks.append(check("service_ExecStart_archive", has_execstart, "ExecStart→archive.sh present" if has_execstart else "Missing ExecStart with archive.sh"))

        # Check: StandardOutput=journal and StandardError=journal
        has_stdout_journal = bool(re.search(r"StandardOutput\s*=\s*journal", service))
        has_stderr_journal = bool(re.search(r"StandardError\s*=\s*journal", service))
        checks.append(check("service_journal_logging",
            has_stdout_journal and has_stderr_journal,
            "Journal logging set" if (has_stdout_journal and has_stderr_journal) else "Missing StandardOutput/StandardError=journal"
        ))
    else:
        for n in ["service_has_Unit_section", "service_has_Service_section", "service_Type_oneshot", "service_ExecStart_archive", "service_journal_logging"]:
            checks.append(check(n, False, "archive.service not found"))

    # ═══════════════════════════════════════════════════════════════
    # SYSTEMD TIMER CHECKS
    # ═══════════════════════════════════════════════════════════════

    checks.append(check(
        "timer_file_exists",
        timer is not None,
        f"Found at: {timer_path}" if timer_path else "archive.timer not found"
    ))

    if timer:
        # Check: [Timer] section
        has_timer_section = "[Timer]" in timer
        checks.append(check("timer_has_Timer_section", has_timer_section, "[Timer] present" if has_timer_section else "Missing [Timer]"))

        # Check: OnCalendar set to 3 AM daily
        # Acceptable: *-*-* 03:00:00 or daily variant pointing to 3AM
        on_cal_match = re.search(r"OnCalendar\s*=\s*(.+)", timer)
        on_cal_ok = False
        on_cal_detail = "OnCalendar not found"
        if on_cal_match:
            val = on_cal_match.group(1).strip()
            on_cal_detail = f"OnCalendar={val}"
            # Accept: *-*-* 03:00:00
            if re.search(r"\*-\*-\*\s+03:00:00", val):
                on_cal_ok = True
        checks.append(check("timer_OnCalendar_3AM_daily", on_cal_ok, on_cal_detail))

        # Check: Persistent=true
        has_persistent = bool(re.search(r"Persistent\s*=\s*true", timer, re.IGNORECASE))
        checks.append(check("timer_Persistent_true", has_persistent, "Persistent=true present" if has_persistent else "Missing Persistent=true"))

        # Check: RandomizedDelaySec=300 (up to 5 min)
        rand_match = re.search(r"RandomizedDelaySec\s*=\s*(\d+)", timer)
        rand_ok = False
        rand_detail = "RandomizedDelaySec not found"
        if rand_match:
            val = int(rand_match.group(1))
            rand_detail = f"RandomizedDelaySec={val}"
            rand_ok = (1 <= val <= 300)  # up to 5 minutes = 300s
        checks.append(check("timer_RandomizedDelaySec_set", rand_ok, rand_detail))

        # Check: [Install] WantedBy=timers.target
        has_install = "[Install]" in timer
        has_wanted_by = bool(re.search(r"WantedBy\s*=\s*timers\.target", timer))
        checks.append(check("timer_Install_WantedBy_timers_target",
            has_install and has_wanted_by,
            "WantedBy=timers.target present" if (has_install and has_wanted_by) else "Missing [Install] or WantedBy=timers.target"
        ))

    else:
        for n in ["timer_has_Timer_section", "timer_OnCalendar_3AM_daily", "timer_Persistent_true", "timer_RandomizedDelaySec_set", "timer_Install_WantedBy_timers_target"]:
            checks.append(check(n, False, "archive.timer not found"))

    # ═══════════════════════════════════════════════════════════════
    # JOB WRAPPER CHECKS
    # ═══════════════════════════════════════════════════════════════

    checks.append(check(
        "wrapper_script_exists",
        wrapper is not None and "NOT IMPLEMENTED" not in wrapper,
        "job_wrapper.sh implemented" if (wrapper and "NOT IMPLEMENTED" not in wrapper) else "job_wrapper.sh missing or still contains placeholder"
    ))

    if wrapper and "NOT IMPLEMENTED" not in wrapper:
        # Check: LOG_DIR or LOG_FILE variable for logging
        has_log = bool(re.search(r"LOG_DIR|LOG_FILE", wrapper))
        checks.append(check("wrapper_has_log_path", has_log, "LOG_DIR/LOG_FILE variable present" if has_log else "No log path variable"))

        # Check: Timestamps on log entries (date -u or date +)
        has_timestamp = bool(re.search(r"date\s+.*%Y|date\s+-u", wrapper))
        checks.append(check("wrapper_logs_timestamps", has_timestamp, "Timestamp logging present" if has_timestamp else "No timestamp in log"))

        # Check: start time capture for elapsed calculation
        has_start_time = bool(re.search(r"START_TIME|start_time", wrapper, re.IGNORECASE))
        checks.append(check("wrapper_captures_start_time", has_start_time, "START_TIME variable present" if has_start_time else "Missing start time capture"))

        # Check: exit code captured and logged
        has_exit_code = bool(re.search(r"EXIT_CODE|exit_code|\$\?", wrapper, re.IGNORECASE))
        checks.append(check("wrapper_captures_exit_code", has_exit_code, "Exit code captured" if has_exit_code else "Exit code not captured"))

        # Check: SUCCESS and FAILED log entries
        has_success_log = bool(re.search(r"SUCCESS", wrapper))
        has_failed_log = bool(re.search(r"FAIL|FAILED|fail", wrapper))
        checks.append(check("wrapper_logs_success_and_failure",
            has_success_log and has_failed_log,
            "SUCCESS and FAIL log entries present" if (has_success_log and has_failed_log) else f"Missing: {'SUCCESS ' if not has_success_log else ''}{'FAIL' if not has_failed_log else ''}"
        ))

        # Check: set -euo pipefail or equivalent error handling
        has_strict = bool(re.search(r"set\s+-[a-z]*e[a-z]*|set\s+-e", wrapper))
        checks.append(check("wrapper_has_set_e", has_strict, "set -e present" if has_strict else "Missing set -euo pipefail"))

    else:
        for n in ["wrapper_has_log_path", "wrapper_logs_timestamps", "wrapper_captures_start_time", "wrapper_captures_exit_code", "wrapper_logs_success_and_failure", "wrapper_has_set_e"]:
            checks.append(check(n, False, "job_wrapper.sh not implemented"))

    # ═══════════════════════════════════════════════════════════════
    # SCORING
    # ═══════════════════════════════════════════════════════════════

    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3) if total > 0 else 0.0
    all_passed = passed_count == total

    return {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))