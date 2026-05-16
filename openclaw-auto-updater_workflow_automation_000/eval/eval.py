import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0
    max_checks = 8

    # --- Helper: find the call log ---
    call_log_path = workspace / "openclaw_call_log.txt"

    # --- Also search for any agent-created output file (scheduled_task.txt) ---
    output_files = list(workspace.rglob("scheduled_task.txt"))

    # =========================================================
    # CHECK 0: openclaw was actually invoked (call log exists)
    # =========================================================
    try:
        if not call_log_path.exists():
            checks.append({
                "name": "openclaw_was_invoked",
                "passed": False,
                "detail": "openclaw_call_log.txt not found — openclaw binary was never called."
            })
            # All subsequent checks will fail; emit early
            for name in [
                "cron_add_subcommand", "name_flag", "cron_expression_weekday",
                "timezone_flag", "session_isolated", "wake_now", "deliver_flag",
                "message_content_dryrun", "output_file_exists"
            ]:
                checks.append({"name": name, "passed": False, "detail": "openclaw was never called."})
            score = 0.0
            return {"passed": False, "score": score, "checks": checks}

        raw_log = call_log_path.read_text()
        checks.append({
            "name": "openclaw_was_invoked",
            "passed": True,
            "detail": f"openclaw_call_log.txt found with {len(raw_log)} bytes."
        })
        total_score += 1
    except Exception as e:
        checks.append({"name": "openclaw_was_invoked", "passed": False, "detail": str(e)})
        raw_log = ""

    # =========================================================
    # CHECK 1: 'cron add' subcommand was used
    # =========================================================
    try:
        cron_add_used = "CRON_ADD_INVOKED=true" in raw_log or "cron add" in raw_log.lower()
        checks.append({
            "name": "cron_add_subcommand",
            "passed": cron_add_used,
            "detail": "'cron add' subcommand detected in call log." if cron_add_used else "'cron add' subcommand NOT detected."
        })
        if cron_add_used:
            total_score += 1
    except Exception as e:
        checks.append({"name": "cron_add_subcommand", "passed": False, "detail": str(e)})

    # =========================================================
    # CHECK 2: --name flag present (any reasonable name)
    # =========================================================
    try:
        name_match = re.search(r'--name\s+["\']?([^"\']+)["\']?', raw_log)
        name_present = name_match is not None
        checks.append({
            "name": "name_flag",
            "passed": name_present,
            "detail": f"--name flag found: '{name_match.group(1).strip()}'" if name_present else "--name flag NOT found."
        })
        if name_present:
            total_score += 1
    except Exception as e:
        checks.append({"name": "name_flag", "passed": False, "detail": str(e)})

    # =========================================================
    # CHECK 3: --cron expression for weekdays only (Mon-Fri)
    # Valid patterns: "15 2 * * 1-5" or "15 2 * * MON-FRI" etc.
    # The task specifies weekday-only, 02:15 Berlin time.
    # =========================================================
    try:
        # Look for --cron "..." in the log
        cron_match = re.search(r'--cron\s+["\']?([^"\']+)["\']?', raw_log)
        if cron_match:
            cron_val = cron_match.group(1).strip().strip("'\"")
            # Must be 5-field cron expression
            fields = cron_val.split()
            weekday_correct = False
            time_correct = False
            if len(fields) == 5:
                minute, hour, dom, month, dow = fields
                # Minute = 15, Hour = 2
                time_correct = (minute == "15" and hour == "2")
                # Day of week = 1-5 or MON-FRI variants
                weekday_correct = dow in ["1-5", "MON-FRI", "mon-fri", "Mon-Fri"]
            cron_ok = weekday_correct and time_correct
            checks.append({
                "name": "cron_expression_weekday",
                "passed": cron_ok,
                "detail": f"Cron expression: '{cron_val}'. Time correct: {time_correct}, Weekday correct: {weekday_correct}"
            })
            if cron_ok:
                total_score += 1
        else:
            checks.append({
                "name": "cron_expression_weekday",
                "passed": False,
                "detail": "--cron flag not found in call log."
            })
    except Exception as e:
        checks.append({"name": "cron_expression_weekday", "passed": False, "detail": str(e)})

    # =========================================================
    # CHECK 4: --tz with IANA timezone name "Europe/Berlin"
    # Must NOT use "CET", "UTC+1", etc.
    # =========================================================
    try:
        tz_match = re.search(r'--tz\s+["\']?([^"\']+)["\']?', raw_log)
        if tz_match:
            tz_val = tz_match.group(1).strip().strip("'\"")
            tz_correct = (tz_val == "Europe/Berlin")
            checks.append({
                "name": "timezone_flag",
                "passed": tz_correct,
                "detail": f"--tz value: '{tz_val}'. Expected 'Europe/Berlin'."
            })
            if tz_correct:
                total_score += 1
        else:
            checks.append({
                "name": "timezone_flag",
                "passed": False,
                "detail": "--tz flag not found."
            })
    except Exception as e:
        checks.append({"name": "timezone_flag", "passed": False, "detail": str(e)})

    # =========================================================
    # CHECK 5: --session isolated (proprietary flag)
    # =========================================================
    try:
        session_ok = "--session isolated" in raw_log or ("--session" in raw_log and "isolated" in raw_log)
        checks.append({
            "name": "session_isolated",
            "passed": session_ok,
            "detail": "'--session isolated' found." if session_ok else "'--session isolated' NOT found in call log."
        })
        if session_ok:
            total_score += 1
    except Exception as e:
        checks.append({"name": "session_isolated", "passed": False, "detail": str(e)})

    # =========================================================
    # CHECK 6: --wake now (proprietary flag)
    # =========================================================
    try:
        wake_ok = "--wake now" in raw_log or ("--wake" in raw_log and "now" in raw_log)
        checks.append({
            "name": "wake_now",
            "passed": wake_ok,
            "detail": "'--wake now' found." if wake_ok else "'--wake now' NOT found."
        })
        if wake_ok:
            total_score += 1
    except Exception as e:
        checks.append({"name": "wake_now", "passed": False, "detail": str(e)})

    # =========================================================
    # CHECK 7: --deliver flag present (proprietary flag)
    # =========================================================
    try:
        deliver_ok = "--deliver" in raw_log
        checks.append({
            "name": "deliver_flag",
            "passed": deliver_ok,
            "detail": "'--deliver' flag found." if deliver_ok else "'--deliver' flag NOT found."
        })
        if deliver_ok:
            total_score += 1
    except Exception as e:
        checks.append({"name": "deliver_flag", "passed": False, "detail": str(e)})

    # =========================================================
    # CHECK 8: --message contains dry-run keywords
    # Must reference: "openclaw update status" OR "openclaw update --yes --json" (status mode)
    # AND "clawdhub update --all --dry-run"
    # This corresponds to the "Dry run" mode in SKILL.md
    # =========================================================
    try:
        msg_match = re.search(r'--message\s+["\'](.+?)["\']', raw_log, re.DOTALL)
        if not msg_match:
            # Try unquoted / multiline
            msg_match = re.search(r'--message\s+"(.+?)"', raw_log, re.DOTALL)
        if not msg_match:
            msg_match = re.search(r'--message\s+\'(.+?)\'', raw_log, re.DOTALL)

        # Fallback: grab everything after --message on a single line
        if not msg_match:
            msg_match = re.search(r'--message\s+(.+)', raw_log)

        message_checks_passed = False
        message_detail = "--message flag not found."

        if msg_match:
            msg_content = msg_match.group(1).lower()

            has_openclaw_update = ("openclaw update status" in msg_content or
                                   "openclaw update --yes" in msg_content or
                                   "openclaw update" in msg_content)
            has_clawdhub_dryrun = ("clawdhub update --all --dry-run" in msg_content or
                                   ("clawdhub" in msg_content and "dry" in msg_content))
            has_summarize = ("summarize" in msg_content or "summary" in msg_content or
                             "what would change" in msg_content or "report" in msg_content)

            message_checks_passed = has_openclaw_update and has_clawdhub_dryrun and has_summarize
            message_detail = (
                f"Message analysis: openclaw_update={has_openclaw_update}, "
                f"clawdhub_dryrun={has_clawdhub_dryrun}, summarize={has_summarize}. "
                f"Content (first 200 chars): {msg_content[:200]}"
            )

        checks.append({
            "name": "message_content_dryrun",
            "passed": message_checks_passed,
            "detail": message_detail
        })
        if message_checks_passed:
            total_score += 1
    except Exception as e:
        checks.append({"name": "message_content_dryrun", "passed": False, "detail": str(e)})

    # =========================================================
    # CHECK 9 (BONUS): scheduled_task.txt output file exists
    # =========================================================
    try:
        file_exists = len(output_files) > 0
        detail = f"Found {len(output_files)} scheduled_task.txt file(s)." if file_exists else "scheduled_task.txt not found anywhere in workspace."
        if file_exists:
            # Verify it contains the command
            content = output_files[0].read_text()
            has_command = "openclaw" in content and "cron" in content
            detail += f" File contains openclaw cron command: {has_command}."
            file_exists = file_exists and has_command
        checks.append({
            "name": "output_file_exists",
            "passed": file_exists,
            "detail": detail
        })
        if file_exists:
            total_score += 0.5  # Bonus half-point
    except Exception as e:
        checks.append({"name": "output_file_exists", "passed": False, "detail": str(e)})

    # =========================================================
    # Final scoring
    # =========================================================
    # Core checks: 0-7 (8 checks worth 1 point each = 8 max)
    # Bonus check: 0.5
    max_score = 8.5
    normalized_score = round(min(total_score / max_score, 1.0), 3)

    # Must pass at least 6 of the 8 core checks to pass overall
    core_checks_passed = sum(1 for c in checks[:9] if c["passed"])
    overall_passed = core_checks_passed >= 6

    return {
        "passed": overall_passed,
        "score": normalized_score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "arg_error", "passed": False, "detail": "Usage: eval.py <workspace_dir>"}]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))