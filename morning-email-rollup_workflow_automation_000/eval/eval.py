#!/usr/bin/env python3
"""
Evaluation script for the morning-email-rollup configuration task.
Tests:
1. rollup.sh has MAX_EMAILS default changed to 5
2. rollup.sh search query changed to 'is:important is:unread newer_than:1d' (no starred)
3. rollup.sh summarize prompt changed to shorter style (1 short sentence)
4. cron add was called with correct proprietary flags:
   - --schedule "0 7 * * *" (7am not 8am)
   - --tz "America/Los_Angeles" (Pacific time)
   - --session isolated
   - GOG_ACCOUNT=pm@hedgefund-example.com embedded in --message
5. GOG_ACCOUNT is set to the correct email in the cron message
"""

import sys
import json
import re
from pathlib import Path

def load_file(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []
    
    # ---- Load rollup.sh ----
    rollup_path = Path(workspace) / "skills/morning-email-rollup/rollup.sh"
    rollup_content = load_file(rollup_path)
    
    # ---- Load cron calls log ----
    cron_log_path = Path(workspace) / ".cron_calls.log"
    cron_log = load_file(cron_log_path)
    
    # === CHECK 1: MAX_EMAILS default changed to 5 ===
    check_name = "rollup.sh: MAX_EMAILS default set to 5"
    try:
        if rollup_content is None:
            checks.append({"name": check_name, "passed": False,
                           "detail": "rollup.sh not found at expected path"})
        else:
            # Look for MAX_EMAILS="${MAX_EMAILS:-5}" or MAX_EMAILS=5 or similar
            pattern = r'MAX_EMAILS\s*=\s*["\']?\$\{MAX_EMAILS:-5\}["\']?'
            alt_pattern = r'MAX_EMAILS\s*=\s*["\']?5["\']?'
            passed = bool(re.search(pattern, rollup_content)) or bool(re.search(alt_pattern, rollup_content))
            # Make sure it's NOT still 10
            still_ten = bool(re.search(r'MAX_EMAILS\s*=\s*["\']?\$\{MAX_EMAILS:-10\}["\']?', rollup_content))
            if still_ten:
                passed = False
            checks.append({"name": check_name, "passed": passed,
                           "detail": f"Found MAX_EMAILS pattern: {passed}. Still has :-10: {still_ten}"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # === CHECK 2: Search query changed to unread-only important (no starred) ===
    check_name = "rollup.sh: Gmail search query uses unread-only important emails"
    try:
        if rollup_content is None:
            checks.append({"name": check_name, "passed": False, "detail": "rollup.sh not found"})
        else:
            # Must have is:important is:unread - must NOT have 'is:starred'
            has_unread_important = bool(re.search(r'is:important.*is:unread|is:unread.*is:important', rollup_content))
            has_starred = bool(re.search(r'is:starred', rollup_content))
            passed = has_unread_important and not has_starred
            checks.append({"name": check_name, "passed": passed,
                           "detail": f"has unread+important: {has_unread_important}, has starred (should be False): {has_starred}"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # === CHECK 3: Summarization prompt changed to shorter style ===
    check_name = "rollup.sh: Summarization prompt changed to short/brief style"
    try:
        if rollup_content is None:
            checks.append({"name": check_name, "passed": False, "detail": "rollup.sh not found"})
        else:
            # Should NOT have the original "medium to long length" prompt
            has_medium_long = bool(re.search(r'medium.to.long|medium to long', rollup_content, re.IGNORECASE))
            # Should have short/brief/concise indicator
            has_short = bool(re.search(r'short|brief|concise|1 short sentence|one short', rollup_content, re.IGNORECASE))
            passed = not has_medium_long and has_short
            checks.append({"name": check_name, "passed": passed,
                           "detail": f"has 'medium to long' (should be False): {has_medium_long}, has short indicator: {has_short}"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # === CHECK 4: cron add was called ===
    check_name = "cron: 'cron add' command was invoked"
    try:
        if cron_log is None:
            checks.append({"name": check_name, "passed": False,
                           "detail": "No cron calls log found - cron was never called"})
        else:
            has_add = bool(re.search(r'CALL:.*\badd\b', cron_log))
            checks.append({"name": check_name, "passed": has_add,
                           "detail": f"Found 'add' subcommand in cron calls: {has_add}. Log snippet: {cron_log[:300]}"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # === CHECK 5: cron schedule is 7am (0 7 * * *) ===
    check_name = "cron: schedule set to 7am (0 7 * * *)"
    try:
        if cron_log is None:
            checks.append({"name": check_name, "passed": False, "detail": "No cron calls log found"})
        else:
            # Look for the schedule pattern in cron add calls
            add_lines = [l for l in cron_log.splitlines() if 'add' in l]
            has_7am = any(re.search(r'0 7 \* \* \*|0\s+7\s+\*\s+\*\s+\*', line) for line in add_lines)
            has_8am = any(re.search(r'0 8 \* \* \*|0\s+8\s+\*\s+\*\s+\*', line) for line in add_lines)
            passed = has_7am and not has_8am
            checks.append({"name": check_name, "passed": passed,
                           "detail": f"has 7am schedule: {has_7am}, has 8am (wrong): {has_8am}"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # === CHECK 6: cron timezone is America/Los_Angeles (Pacific) ===
    check_name = "cron: timezone set to America/Los_Angeles (Pacific)"
    try:
        if cron_log is None:
            checks.append({"name": check_name, "passed": False, "detail": "No cron calls log found"})
        else:
            add_lines = [l for l in cron_log.splitlines() if 'add' in l]
            has_pacific = any(re.search(r'America/Los_Angeles|America\/Los_Angeles|US/Pacific', line) for line in add_lines)
            has_denver = any(re.search(r'America/Denver', line) for line in add_lines)
            # Pacific is correct; Denver would be wrong
            passed = has_pacific and not has_denver
            checks.append({"name": check_name, "passed": passed,
                           "detail": f"has Pacific tz: {has_pacific}, has Denver (wrong): {has_denver}"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # === CHECK 7: cron uses --session isolated ===
    check_name = "cron: --session isolated flag present"
    try:
        if cron_log is None:
            checks.append({"name": check_name, "passed": False, "detail": "No cron calls log found"})
        else:
            add_lines = [l for l in cron_log.splitlines() if 'add' in l]
            has_isolated = any(re.search(r'--session\s+isolated|session.*isolated', line) for line in add_lines)
            checks.append({"name": check_name, "passed": has_isolated,
                           "detail": f"Found '--session isolated': {has_isolated}"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # === CHECK 8: cron --message includes GOG_ACCOUNT=pm@hedgefund-example.com ===
    check_name = "cron: --message embeds GOG_ACCOUNT with correct email"
    try:
        if cron_log is None:
            checks.append({"name": check_name, "passed": False, "detail": "No cron calls log found"})
        else:
            add_lines = [l for l in cron_log.splitlines() if 'add' in l]
            # The message must contain GOG_ACCOUNT=pm@hedgefund-example.com
            has_gog_account = any(
                re.search(r'GOG_ACCOUNT\s*=\s*pm@hedgefund-example\.com', line)
                for line in add_lines
            )
            checks.append({"name": check_name, "passed": has_gog_account,
                           "detail": f"Found GOG_ACCOUNT=pm@hedgefund-example.com in cron message: {has_gog_account}. Lines checked: {add_lines[:2]}"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # === CHECK 9: cron --message includes the rollup.sh path ===
    check_name = "cron: --message invokes rollup.sh (not some other script)"
    try:
        if cron_log is None:
            checks.append({"name": check_name, "passed": False, "detail": "No cron calls log found"})
        else:
            add_lines = [l for l in cron_log.splitlines() if 'add' in l]
            has_rollup = any(re.search(r'rollup\.sh', line) for line in add_lines)
            checks.append({"name": check_name, "passed": has_rollup,
                           "detail": f"Found rollup.sh in cron message: {has_rollup}"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # === SCORING ===
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4) if total > 0 else 0.0
    overall_passed = passed_count == total

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()