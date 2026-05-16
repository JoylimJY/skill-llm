import sys
import json
import re
from pathlib import Path

def find_script(workspace: Path) -> Path | None:
    candidates = list(workspace.rglob("fix_cron_jobs.sh"))
    if candidates:
        return candidates[0]
    return None

def check(name: str, passed: bool, detail: str) -> dict:
    return {"name": name, "passed": passed, "detail": detail}

def run_checks(script_text: str) -> list[dict]:
    checks = []
    text = script_text

    # ── COMMAND 1: Recurring standup job ─────────────────────────────────

    # 1a. Must NOT invoke 'cron' tool directly (no bare "cron add" or "cron list" as a command)
    #     Allowed patterns: clawdbot cron add (via exec or direct shell call)
    #     Forbidden patterns: lines that call `cron add` or `cron list` as a standalone command
    bare_cron_pattern = re.compile(r'(?<!\w)(cron\s+(add|list|run|show|rm))', re.MULTILINE)
    # Filter out lines that have clawdbot before cron
    lines = text.splitlines()
    bare_cron_violations = []
    for line in lines:
        stripped = line.strip()
        # Skip comments
        if stripped.startswith('#'):
            continue
        # Find bare `cron add` / `cron list` without clawdbot prefix
        if re.search(r'(?<![a-zA-Z0-9_/-])cron\s+(add|list|run|show|rm)', stripped):
            if 'clawdbot' not in stripped:
                bare_cron_violations.append(stripped)
    checks.append(check(
        "no_bare_cron_tool_usage",
        len(bare_cron_violations) == 0,
        f"Bare cron tool calls found (must use clawdbot cron via exec/shell): {bare_cron_violations}" if bare_cron_violations else "OK - no bare cron tool invocations"
    ))

    # 1b. Uses clawdbot cron add
    has_clawdbot_cron_add = bool(re.search(r'clawdbot\s+cron\s+add', text))
    checks.append(check(
        "uses_clawdbot_cron_add",
        has_clawdbot_cron_add,
        "Found 'clawdbot cron add'" if has_clawdbot_cron_add else "Missing 'clawdbot cron add' command"
    ))

    # 1c. Recurring job has correct cron expression for weekday 8 AM
    # Accept: "0 8 * * 1-5"
    has_correct_cron_expr = bool(re.search(r'--cron\s+["\']?0\s+8\s+\*\s+\*\s+1-5["\']?', text))
    checks.append(check(
        "correct_cron_expression_weekday_8am",
        has_correct_cron_expr,
        "Found correct cron expression '0 8 * * 1-5'" if has_correct_cron_expr else "Missing or incorrect cron expression for weekday 8 AM (expected: '0 8 * * 1-5')"
    ))

    # 1d. Bolivia timezone: America/La_Paz
    has_bolivia_tz = bool(re.search(r'--tz\s+["\']?America/La_Paz["\']?', text))
    checks.append(check(
        "explicit_bolivia_timezone",
        has_bolivia_tz,
        "Found '--tz America/La_Paz'" if has_bolivia_tz else "Missing '--tz America/La_Paz' (Bolivia timezone required)"
    ))

    # 1e. --session isolated (must be present, not --session main)
    has_session_isolated = bool(re.search(r'--session\s+isolated', text))
    has_session_main = bool(re.search(r'--session\s+main', text))
    session_ok = has_session_isolated and not has_session_main
    checks.append(check(
        "session_isolated_not_main",
        session_ok,
        "Found '--session isolated' and no '--session main'" if session_ok
        else f"Session issue: isolated={'found' if has_session_isolated else 'missing'}, main={'present (WRONG)' if has_session_main else 'absent'}"
    ))

    # 1f. --deliver flag present
    has_deliver = bool(re.search(r'--deliver\b', text))
    checks.append(check(
        "has_deliver_flag",
        has_deliver,
        "Found '--deliver'" if has_deliver else "Missing '--deliver' flag"
    ))

    # 1g. --channel telegram
    has_channel_telegram = bool(re.search(r'--channel\s+telegram', text))
    checks.append(check(
        "channel_telegram",
        has_channel_telegram,
        "Found '--channel telegram'" if has_channel_telegram else "Missing '--channel telegram'"
    ))

    # 1h. --to with correct chat ID
    has_correct_to = bool(re.search(r'--to\s+["\']?-1001234567890["\']?', text))
    checks.append(check(
        "correct_telegram_chat_id",
        has_correct_to,
        "Found '--to -1001234567890'" if has_correct_to else "Missing or incorrect '--to -1001234567890'"
    ))

    # 1i. --best-effort-deliver
    has_best_effort = bool(re.search(r'--best-effort-deliver\b', text))
    checks.append(check(
        "best_effort_deliver",
        has_best_effort,
        "Found '--best-effort-deliver'" if has_best_effort else "Missing '--best-effort-deliver' flag"
    ))

    # 1j. Message contains [INSTRUCTION: DO NOT USE ANY TOOLS] prefix (case-insensitive for DO NOT USE)
    has_instruction_prefix = bool(re.search(
        r'\[INSTRUCTION[:\s]+DO\s+NOT\s+USE\s+ANY\s+TOOLS',
        text, re.IGNORECASE
    ))
    checks.append(check(
        "message_has_no_tools_instruction",
        has_instruction_prefix,
        "Found '[INSTRUCTION: DO NOT USE ANY TOOLS...]' prefix in message" if has_instruction_prefix
        else "Missing '[INSTRUCTION: DO NOT USE ANY TOOLS...]' prefix in message payload"
    ))

    # ── COMMAND 2: One-shot reminder ─────────────────────────────────────

    # 2a. Uses --at "+30m" for one-shot reminder
    has_at_30m = bool(re.search(r'--at\s+["\']?\+30m["\']?', text))
    checks.append(check(
        "oneshot_uses_at_plus_30m",
        has_at_30m,
        "Found '--at +30m' for one-shot reminder" if has_at_30m else "Missing '--at +30m' for one-shot reminder"
    ))

    # 2b. One-shot job uses --delete-after-run
    has_delete_after_run = bool(re.search(r'--delete-after-run\b', text))
    checks.append(check(
        "oneshot_delete_after_run",
        has_delete_after_run,
        "Found '--delete-after-run'" if has_delete_after_run else "Missing '--delete-after-run' for one-shot job"
    ))

    # 2c. One-shot also uses --session isolated (must appear at least twice or once generically)
    # We'll check it appears at least twice (once per job) OR trust the global session check
    session_isolated_count = len(re.findall(r'--session\s+isolated', text))
    checks.append(check(
        "oneshot_also_session_isolated",
        session_isolated_count >= 2,
        f"Found '--session isolated' {session_isolated_count} time(s) (need >=2, one per job)"
        if session_isolated_count >= 2
        else f"'--session isolated' appears only {session_isolated_count} time(s); both jobs need it"
    ))

    # 2d. One-shot also has --best-effort-deliver (check count >= 2 OR at least 1 since it's inherited)
    # Lenient: at least 1 occurrence already checked above. Check for 2 occurrences.
    best_effort_count = len(re.findall(r'--best-effort-deliver\b', text))
    checks.append(check(
        "oneshot_best_effort_deliver",
        best_effort_count >= 2,
        f"Found '--best-effort-deliver' {best_effort_count} time(s) (need >=2, one per job)"
        if best_effort_count >= 2
        else f"'--best-effort-deliver' appears {best_effort_count} time(s); both jobs need it"
    ))

    return checks


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "arg_check", "passed": False, "detail": "No workspace path provided"}
        ]}))
        sys.exit(1)

    workspace = Path(sys.argv[1])
    all_checks = []

    # ── Locate the script ────────────────────────────────────────────────
    script_path = find_script(workspace)
    if script_path is None:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False,
                         "detail": "fix_cron_jobs.sh not found anywhere in workspace"}]
        }))
        return

    all_checks.append({"name": "file_exists", "passed": True,
                        "detail": f"Found at {script_path.relative_to(workspace)}"})

    try:
        script_text = script_path.read_text(encoding="utf-8")
    except Exception as e:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_readable", "passed": False, "detail": str(e)}]
        }))
        return

    all_checks.append({"name": "file_readable", "passed": True, "detail": "File read successfully"})

    # ── Run content checks ───────────────────────────────────────────────
    content_checks = run_checks(script_text)
    all_checks.extend(content_checks)

    # ── Score ────────────────────────────────────────────────────────────
    total = len(all_checks)
    passed_count = sum(1 for c in all_checks if c["passed"])
    score = round(passed_count / total, 4)
    overall_passed = all(c["passed"] for c in all_checks)

    print(json.dumps({
        "passed": overall_passed,
        "score": score,
        "checks": all_checks
    }, indent=2))


if __name__ == "__main__":
    main()