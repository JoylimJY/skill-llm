#!/usr/bin/env python3
"""
Evaluation script for the macOS AppleScript Fallback task.
Checks that the agent correctly invoked:
  1. scripts/create_calendar_event.sh with exact args (title, calendar, start YYYY-MM-DD HH:MM:SS, end YYYY-MM-DD HH:MM:SS)
  2. scripts/create_note.sh with HTML body (<h1> and <p> tags) and account "iCloud"
  3. scripts/send_imessage.sh with recipient as first arg and message as second arg
"""

import sys
import json
import re
from pathlib import Path

def load_log(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return ""

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    logs_dir = workspace / "logs"

    checks = []
    total_score = 0.0
    max_score = 7  # total points available

    # ── Expected values from task_brief.json ─────────────────────────────
    try:
        brief = json.loads((workspace / "task_brief.json").read_text(encoding="utf-8"))
        cal = brief["calendar_event"]
        note = brief["note"]
        msg = brief["imessage"]
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "task_brief_load", "passed": False, "detail": f"Could not load task_brief.json: {e}"}]
        }
        print(json.dumps(result))
        return

    # ══════════════════════════════════════════════════════════════════════
    # CHECK GROUP 1: Calendar Event
    # ══════════════════════════════════════════════════════════════════════
    cal_log_path = logs_dir / "create_calendar_event.log"
    cal_log = load_log(cal_log_path)

    # 1a. Script was invoked at all
    cal_invoked = bool(cal_log.strip())
    checks.append({
        "name": "calendar_script_invoked",
        "passed": cal_invoked,
        "detail": "create_calendar_event.sh was called" if cal_invoked else "create_calendar_event.log is empty or missing — script was never invoked"
    })
    if cal_invoked:
        total_score += 1

    # 1b. Title argument correct (ARG1)
    cal_title_ok = False
    cal_title_detail = "Could not find ARG1 in calendar log"
    try:
        # Extract ARG1 line
        arg1_match = re.search(r'^ARG1:\s*(.+)$', cal_log, re.MULTILINE)
        if arg1_match:
            arg1_val = arg1_match.group(1).strip()
            cal_title_ok = cal["title"].lower() in arg1_val.lower() or arg1_val.lower() in cal["title"].lower()
            cal_title_detail = f"ARG1='{arg1_val}' expected to contain '{cal['title']}'"
        else:
            cal_title_detail = "No ARG1 line found in calendar log"
    except Exception as e:
        cal_title_detail = f"Exception: {e}"
    checks.append({"name": "calendar_title_correct", "passed": cal_title_ok, "detail": cal_title_detail})
    if cal_title_ok:
        total_score += 0.5

    # 1c. Calendar name argument correct (ARG2 = "Work")
    cal_name_ok = False
    cal_name_detail = "Could not find ARG2 in calendar log"
    try:
        arg2_match = re.search(r'^ARG2:\s*(.+)$', cal_log, re.MULTILINE)
        if arg2_match:
            arg2_val = arg2_match.group(1).strip()
            cal_name_ok = arg2_val.strip('"\'').strip() == cal["calendar"]
            cal_name_detail = f"ARG2='{arg2_val}' expected '{cal['calendar']}'"
    except Exception as e:
        cal_name_detail = f"Exception: {e}"
    checks.append({"name": "calendar_name_correct", "passed": cal_name_ok, "detail": cal_name_detail})
    if cal_name_ok:
        total_score += 0.5

    # 1d. Start datetime in YYYY-MM-DD HH:MM:SS format (locale-safe)
    cal_start_ok = False
    cal_start_detail = "Could not find ARG3 in calendar log"
    DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$')
    try:
        arg3_match = re.search(r'^ARG3:\s*(.+)$', cal_log, re.MULTILINE)
        if arg3_match:
            arg3_val = arg3_match.group(1).strip().strip('"\'')
            cal_start_ok = bool(DATE_PATTERN.match(arg3_val)) and arg3_val == cal["start"]
            cal_start_detail = f"ARG3='{arg3_val}' expected '{cal['start']}' in YYYY-MM-DD HH:MM:SS format"
    except Exception as e:
        cal_start_detail = f"Exception: {e}"
    checks.append({"name": "calendar_start_datetime_format", "passed": cal_start_ok, "detail": cal_start_detail})
    if cal_start_ok:
        total_score += 0.5

    # 1e. End datetime in YYYY-MM-DD HH:MM:SS format
    cal_end_ok = False
    cal_end_detail = "Could not find ARG4 in calendar log"
    try:
        arg4_match = re.search(r'^ARG4:\s*(.+)$', cal_log, re.MULTILINE)
        if arg4_match:
            arg4_val = arg4_match.group(1).strip().strip('"\'')
            cal_end_ok = bool(DATE_PATTERN.match(arg4_val)) and arg4_val == cal["end"]
            cal_end_detail = f"ARG4='{arg4_val}' expected '{cal['end']}' in YYYY-MM-DD HH:MM:SS format"
    except Exception as e:
        cal_end_detail = f"Exception: {e}"
    checks.append({"name": "calendar_end_datetime_format", "passed": cal_end_ok, "detail": cal_end_detail})
    if cal_end_ok:
        total_score += 0.5

    # ══════════════════════════════════════════════════════════════════════
    # CHECK GROUP 2: Notes
    # ══════════════════════════════════════════════════════════════════════
    note_log_path = logs_dir / "create_note.log"
    note_log = load_log(note_log_path)

    # 2a. Script was invoked
    note_invoked = bool(note_log.strip())
    checks.append({
        "name": "note_script_invoked",
        "passed": note_invoked,
        "detail": "create_note.sh was called" if note_invoked else "create_note.log is empty or missing — script was never invoked"
    })
    if note_invoked:
        total_score += 1

    # 2b. Body argument uses HTML (must contain <h1> or <p> tags) — PROPRIETARY TRAP
    note_html_ok = False
    note_html_detail = "Could not find ARG1 in note log"
    try:
        arg1_match = re.search(r'^ARG1:\s*(.+)$', note_log, re.MULTILINE)
        if arg1_match:
            arg1_val = arg1_match.group(1).strip()
            # Must contain at least one HTML tag from the required set
            has_h1 = bool(re.search(r'<h1[\s>]', arg1_val, re.IGNORECASE))
            has_p = bool(re.search(r'<p[\s>]', arg1_val, re.IGNORECASE))
            note_html_ok = has_h1 or has_p
            note_html_detail = f"ARG1 body HTML check: has_h1={has_h1}, has_p={has_p}. Value starts with: '{arg1_val[:80]}'"
        else:
            note_html_detail = "No ARG1 line found in note log"
    except Exception as e:
        note_html_detail = f"Exception: {e}"
    checks.append({"name": "note_body_is_html", "passed": note_html_ok, "detail": note_html_detail})
    if note_html_ok:
        total_score += 1

    # 2c. Account argument is "iCloud" (ARG2) — PROPRIETARY TRAP
    note_account_ok = False
    note_account_detail = "Could not find ARG2 in note log"
    try:
        arg2_match = re.search(r'^ARG2:\s*(.+)$', note_log, re.MULTILINE)
        if arg2_match:
            arg2_val = arg2_match.group(1).strip().strip('"\'')
            note_account_ok = arg2_val == note["account"]
            note_account_detail = f"ARG2='{arg2_val}' expected '{note['account']}'"
        else:
            note_account_detail = "No ARG2 line found in note log"
    except Exception as e:
        note_account_detail = f"Exception: {e}"
    checks.append({"name": "note_account_is_icloud", "passed": note_account_ok, "detail": note_account_detail})
    if note_account_ok:
        total_score += 0.5

    # ══════════════════════════════════════════════════════════════════════
    # CHECK GROUP 3: iMessage
    # ══════════════════════════════════════════════════════════════════════
    imsg_log_path = logs_dir / "send_imessage.log"
    imsg_log = load_log(imsg_log_path)

    # 3a. Script was invoked
    imsg_invoked = bool(imsg_log.strip())
    checks.append({
        "name": "imessage_script_invoked",
        "passed": imsg_invoked,
        "detail": "send_imessage.sh was called" if imsg_invoked else "send_imessage.log is empty or missing — script was never invoked"
    })
    if imsg_invoked:
        total_score += 1

    # 3b. Recipient (ARG1) is correct Apple ID / email — PROPRIETARY TRAP (buddy arg must come first)
    imsg_recipient_ok = False
    imsg_recipient_detail = "Could not find ARG1 in imessage log"
    try:
        arg1_match = re.search(r'^ARG1:\s*(.+)$', imsg_log, re.MULTILINE)
        if arg1_match:
            arg1_val = arg1_match.group(1).strip().strip('"\'')
            imsg_recipient_ok = msg["recipient"] in arg1_val
            imsg_recipient_detail = f"ARG1='{arg1_val}' expected to contain '{msg['recipient']}'"
        else:
            imsg_recipient_detail = "No ARG1 line found in imessage log"
    except Exception as e:
        imsg_recipient_detail = f"Exception: {e}"
    checks.append({"name": "imessage_recipient_first_arg", "passed": imsg_recipient_ok, "detail": imsg_recipient_detail})
    if imsg_recipient_ok:
        total_score += 0.5

    # 3c. Message text (ARG2) is non-empty and relevant
    imsg_msg_ok = False
    imsg_msg_detail = "Could not find ARG2 in imessage log"
    try:
        arg2_match = re.search(r'^ARG2:\s*(.+)$', imsg_log, re.MULTILINE)
        if arg2_match:
            arg2_val = arg2_match.group(1).strip()
            # Message should be non-trivial and mention Singapore or the summit or Sarah
            keywords = ["singapore", "summit", "sarah", "keynote", "july", "confirmed", "david"]
            imsg_msg_ok = any(kw in arg2_val.lower() for kw in keywords) and len(arg2_val) > 20
            imsg_msg_detail = f"ARG2 message='{arg2_val[:100]}' keyword check passed={imsg_msg_ok}"
        else:
            imsg_msg_detail = "No ARG2 line found in imessage log"
    except Exception as e:
        imsg_msg_detail = f"Exception: {e}"
    checks.append({"name": "imessage_message_content", "passed": imsg_msg_ok, "detail": imsg_msg_detail})
    if imsg_msg_ok:
        total_score += 0.5

    # ── Final scoring ──────────────────────────────────────────────────
    final_score = round(total_score / max_score, 4)
    all_critical_passed = cal_invoked and note_invoked and imsg_invoked and note_html_ok
    passed = all_critical_passed and final_score >= 0.7

    result = {
        "passed": passed,
        "score": final_score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()