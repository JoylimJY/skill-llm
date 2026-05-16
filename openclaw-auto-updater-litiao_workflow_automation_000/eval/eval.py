import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    workspace_path = Path(workspace)

    # ------------------------------------------------------------------ #
    # Helper
    # ------------------------------------------------------------------ #
    def add_check(name: str, passed: bool, detail: str):
        checks.append({"name": name, "passed": passed, "detail": detail})

    # ------------------------------------------------------------------ #
    # CHECK 1: Was 'openclaw cron add' actually called?
    # ------------------------------------------------------------------ #
    cron_calls_file = workspace_path / ".cron_add_calls.txt"
    raw_calls = ""
    try:
        raw_calls = cron_calls_file.read_text()
        has_cron_add = "cron" in raw_calls and "add" in raw_calls
        add_check(
            "openclaw_cron_add_called",
            has_cron_add,
            f"openclaw cron add was {'found' if has_cron_add else 'NOT found'} in recorded calls."
        )
    except Exception as e:
        add_check("openclaw_cron_add_called", False, f"Could not read cron calls log: {e}")

    # ------------------------------------------------------------------ #
    # CHECK 2: --name flag present and non-empty
    # ------------------------------------------------------------------ #
    try:
        name_match = re.search(r'--name\s+"([^"]+)"', raw_calls) or \
                     re.search(r"--name\s+'([^']+)'", raw_calls) or \
                     re.search(r'--name\s+([^\s-][^\s]*)', raw_calls)
        has_name = name_match is not None
        detail = f"--name value: '{name_match.group(1)}'" if name_match else "--name flag not found or empty"
        add_check("flag_name_present", has_name, detail)
    except Exception as e:
        add_check("flag_name_present", False, f"Error checking --name: {e}")

    # ------------------------------------------------------------------ #
    # CHECK 3: --cron set to daily 03:30 ("30 3 * * *")
    # ------------------------------------------------------------------ #
    try:
        cron_match = re.search(r'--cron\s+"([^"]+)"', raw_calls) or \
                     re.search(r"--cron\s+'([^']+)'", raw_calls) or \
                     re.search(r'--cron\s+(\S+)', raw_calls)
        cron_val = cron_match.group(1) if cron_match else ""
        # Accept "30 3 * * *" (daily at 03:30)
        correct_cron = cron_val.strip() == "30 3 * * *"
        add_check(
            "flag_cron_daily_0330",
            correct_cron,
            f"--cron value: '{cron_val}' (expected '30 3 * * *')"
        )
    except Exception as e:
        add_check("flag_cron_daily_0330", False, f"Error checking --cron: {e}")

    # ------------------------------------------------------------------ #
    # CHECK 4: --tz set to Europe/Berlin
    # ------------------------------------------------------------------ #
    try:
        tz_match = re.search(r'--tz\s+"([^"]+)"', raw_calls) or \
                   re.search(r"--tz\s+'([^']+)'", raw_calls) or \
                   re.search(r'--tz\s+(\S+)', raw_calls)
        tz_val = tz_match.group(1) if tz_match else ""
        correct_tz = "Europe/Berlin" in tz_val
        add_check(
            "flag_tz_europe_berlin",
            correct_tz,
            f"--tz value: '{tz_val}' (expected 'Europe/Berlin')"
        )
    except Exception as e:
        add_check("flag_tz_europe_berlin", False, f"Error checking --tz: {e}")

    # ------------------------------------------------------------------ #
    # CHECK 5: --session isolated (proprietary trap #1)
    # ------------------------------------------------------------------ #
    try:
        session_match = re.search(r'--session\s+"([^"]+)"', raw_calls) or \
                        re.search(r"--session\s+'([^']+)'", raw_calls) or \
                        re.search(r'--session\s+(\S+)', raw_calls)
        session_val = session_match.group(1) if session_match else ""
        correct_session = "isolated" in session_val
        add_check(
            "flag_session_isolated",
            correct_session,
            f"--session value: '{session_val}' (expected 'isolated') — proprietary flag"
        )
    except Exception as e:
        add_check("flag_session_isolated", False, f"Error checking --session: {e}")

    # ------------------------------------------------------------------ #
    # CHECK 6: --wake now (proprietary trap #2)
    # ------------------------------------------------------------------ #
    try:
        wake_match = re.search(r'--wake\s+"([^"]+)"', raw_calls) or \
                     re.search(r"--wake\s+'([^']+)'", raw_calls) or \
                     re.search(r'--wake\s+(\S+)', raw_calls)
        wake_val = wake_match.group(1) if wake_match else ""
        correct_wake = "now" in wake_val
        add_check(
            "flag_wake_now",
            correct_wake,
            f"--wake value: '{wake_val}' (expected 'now') — proprietary flag"
        )
    except Exception as e:
        add_check("flag_wake_now", False, f"Error checking --wake: {e}")

    # ------------------------------------------------------------------ #
    # CHECK 7: --deliver flag present (boolean, no argument)
    # ------------------------------------------------------------------ #
    try:
        has_deliver = "--deliver" in raw_calls
        add_check(
            "flag_deliver_present",
            has_deliver,
            f"--deliver flag {'found' if has_deliver else 'NOT found'} in call."
        )
    except Exception as e:
        add_check("flag_deliver_present", False, f"Error checking --deliver: {e}")

    # ------------------------------------------------------------------ #
    # CHECK 8: --message includes required update commands
    # The message must include both:
    #   - "openclaw update --yes --json"
    #   - "clawdhub update --all"  (note spelling: clawdhub)
    # ------------------------------------------------------------------ #
    try:
        # Extract message content - it's a quoted string after --message
        msg_match = re.search(r'--message\s+"(.*?)"', raw_calls, re.DOTALL) or \
                    re.search(r"--message\s+'(.*?)'", raw_calls, re.DOTALL)
        msg_val = msg_match.group(1) if msg_match else raw_calls  # fallback to full

        has_openclaw_update = "openclaw update --yes --json" in msg_val
        has_clawdhub_update = "clawdhub update --all" in msg_val

        add_check(
            "message_contains_openclaw_update",
            has_openclaw_update,
            f"'openclaw update --yes --json' {'found' if has_openclaw_update else 'NOT found'} in --message"
        )
        add_check(
            "message_contains_clawdhub_update",
            has_clawdhub_update,
            f"'clawdhub update --all' {'found' if has_clawdhub_update else 'NOT found'} in --message"
        )
    except Exception as e:
        add_check("message_contains_openclaw_update", False, f"Error checking --message content: {e}")
        add_check("message_contains_clawdhub_update", False, f"Error checking --message content: {e}")

    # ------------------------------------------------------------------ #
    # CHECK 9: Summary report file exists with correct format
    # File: update_summary.txt (or .md) anywhere in workspace
    # Must contain: emoji 🔄, arrow →, "Skills updated:", "Skills unchanged:", "Errors:"
    # ------------------------------------------------------------------ #
    summary_files = list(workspace_path.rglob("update_summary.*"))
    summary_content = ""
    try:
        if not summary_files:
            add_check("summary_file_exists", False, "No update_summary.* file found in workspace.")
        else:
            summary_content = summary_files[0].read_text(encoding="utf-8")
            add_check("summary_file_exists", True, f"Found summary file: {summary_files[0]}")
    except Exception as e:
        add_check("summary_file_exists", False, f"Error reading summary file: {e}")

    # CHECK 9a: Contains the 🔄 emoji
    try:
        has_emoji = "🔄" in summary_content
        add_check(
            "summary_has_update_emoji",
            has_emoji,
            f"🔄 emoji {'found' if has_emoji else 'NOT found'} in summary."
        )
    except Exception as e:
        add_check("summary_has_update_emoji", False, f"Error: {e}")

    # CHECK 9b: Contains arrow notation (→) for version change
    try:
        has_arrow = "→" in summary_content
        add_check(
            "summary_has_arrow_notation",
            has_arrow,
            f"→ arrow {'found' if has_arrow else 'NOT found'} in summary (required for version change display)."
        )
    except Exception as e:
        add_check("summary_has_arrow_notation", False, f"Error: {e}")

    # CHECK 9c: Contains required field labels
    try:
        has_skills_updated = "Skills updated:" in summary_content
        has_skills_unchanged = "Skills unchanged:" in summary_content
        has_errors = "Errors:" in summary_content
        all_fields = has_skills_updated and has_skills_unchanged and has_errors
        add_check(
            "summary_has_required_fields",
            all_fields,
            f"Fields - 'Skills updated:': {has_skills_updated}, "
            f"'Skills unchanged:': {has_skills_unchanged}, "
            f"'Errors:': {has_errors}"
        )
    except Exception as e:
        add_check("summary_has_required_fields", False, f"Error: {e}")

    # CHECK 9d: Contains OpenClaw version line with status OK
    try:
        has_openclaw_line = bool(re.search(r'OpenClaw:.*→.*(OK)', summary_content))
        add_check(
            "summary_has_openclaw_version_ok",
            has_openclaw_line,
            f"'OpenClaw: X → Y (OK)' pattern {'found' if has_openclaw_line else 'NOT found'} in summary."
        )
    except Exception as e:
        add_check("summary_has_openclaw_version_ok", False, f"Error: {e}")

    # ------------------------------------------------------------------ #
    # Final scoring
    # ------------------------------------------------------------------ #
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4) if total > 0 else 0.0
    overall_passed = score >= 0.85  # Must pass at least 85% of checks

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))