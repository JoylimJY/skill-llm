import json
import sys
import re
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

checks = []
total_score = 0.0

def load_json(path):
    with open(path) as f:
        return json.load(f)

def read_text(path):
    with open(path) as f:
        return f.read()

# -------------------------------------------------------------------------
# Load state files
# -------------------------------------------------------------------------
try:
    added_reminders = load_json(workspace / "added_reminders.json")
    cli_log_text = read_text(workspace / "cli_calls.log")
    cli_calls = []
    for line in cli_log_text.strip().splitlines():
        line = line.strip()
        if line:
            try:
                cli_calls.append(json.loads(line))
            except:
                pass
except Exception as e:
    checks.append({"name": "state_files_readable", "passed": False, "detail": f"Could not read state files: {e}"})
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

# -------------------------------------------------------------------------
# Helper: find reminder by title substring
# -------------------------------------------------------------------------
def find_reminder(title_substr):
    for r in added_reminders:
        if title_substr.lower() in r.get("title", "").lower():
            return r
    return None

def find_cli_calls_with_command(cmd):
    return [c for c in cli_calls if c.get("args") and c["args"][0] == cmd]

# -------------------------------------------------------------------------
# CHECK 1: parse command was called with --file pointing to meeting_notes.txt
# -------------------------------------------------------------------------
try:
    parse_calls = find_cli_calls_with_command("parse")
    parse_with_file = [c for c in parse_calls if "--file" in c.get("args", [])]
    file_arg_correct = False
    for c in parse_with_file:
        args = c.get("args", [])
        idx = args.index("--file") if "--file" in args else -1
        if idx >= 0 and idx+1 < len(args):
            file_val = args[idx+1]
            if "meeting_notes" in file_val:
                file_arg_correct = True
                break

    passed = len(parse_with_file) > 0 and file_arg_correct
    checks.append({
        "name": "parse_called_with_file",
        "passed": passed,
        "detail": f"parse --file with meeting_notes.txt called: {file_arg_correct}. Total parse-file calls: {len(parse_with_file)}"
    })
    if passed:
        total_score += 0.10
except Exception as e:
    checks.append({"name": "parse_called_with_file", "passed": False, "detail": str(e)})

# -------------------------------------------------------------------------
# CHECK 2: All 4 action items were added (one per parsed item)
# -------------------------------------------------------------------------
try:
    expected_titles = [
        "q1 performance report",
        "engineering standup",
        "api documentation",
        "security audit"
    ]
    found = []
    for t in expected_titles:
        r = find_reminder(t)
        found.append((t, r is not None))

    all_found = all(f for _, f in found)
    checks.append({
        "name": "all_four_items_added",
        "passed": all_found,
        "detail": f"Found reminders: {found}"
    })
    if all_found:
        total_score += 0.15
except Exception as e:
    checks.append({"name": "all_four_items_added", "passed": False, "detail": str(e)})

# -------------------------------------------------------------------------
# CHECK 3: Q1 report has priority=high (from parse output) OR was edited to high
# -------------------------------------------------------------------------
try:
    q1 = find_reminder("q1 performance report")
    if q1 is None:
        q1 = find_reminder("q1 report")
    priority_correct = q1 is not None and q1.get("priority", "").lower() == "high"
    checks.append({
        "name": "q1_report_priority_high",
        "passed": priority_correct,
        "detail": f"Q1 reminder: {q1}"
    })
    if priority_correct:
        total_score += 0.15
except Exception as e:
    checks.append({"name": "q1_report_priority_high", "passed": False, "detail": str(e)})

# -------------------------------------------------------------------------
# CHECK 4: Security audit has priority=high
# -------------------------------------------------------------------------
try:
    sec = find_reminder("security audit")
    priority_correct = sec is not None and sec.get("priority", "").lower() == "high"
    checks.append({
        "name": "security_audit_priority_high",
        "passed": priority_correct,
        "detail": f"Security audit reminder: {sec}"
    })
    if priority_correct:
        total_score += 0.10
except Exception as e:
    checks.append({"name": "security_audit_priority_high", "passed": False, "detail": str(e)})

# -------------------------------------------------------------------------
# CHECK 5 (CRITICAL): Bi-weekly standup uses --repeat weekly --interval 2
# NOT multiple separate add calls for the same standup
# -------------------------------------------------------------------------
try:
    standup = find_reminder("standup")
    if standup is None:
        standup = find_reminder("engineering standup")

    has_repeat_weekly = standup is not None and standup.get("repeat") == "weekly"
    has_interval_2 = standup is not None and standup.get("interval") == 2

    # Also check: did agent NOT create multiple standup reminders (that would be wrong)
    standup_count = sum(
        1 for r in added_reminders
        if "standup" in r.get("title", "").lower()
    )
    no_duplicate_standups = standup_count == 1

    passed = has_repeat_weekly and has_interval_2 and no_duplicate_standups
    checks.append({
        "name": "biweekly_standup_uses_repeat_interval2",
        "passed": passed,
        "detail": (
            f"repeat=weekly: {has_repeat_weekly}, interval=2: {has_interval_2}, "
            f"standup_count={standup_count} (should be 1, not duplicated), "
            f"standup_reminder={standup}"
        )
    })
    if passed:
        total_score += 0.20
except Exception as e:
    checks.append({"name": "biweekly_standup_uses_repeat_interval2", "passed": False, "detail": str(e)})

# -------------------------------------------------------------------------
# CHECK 6: No multiple separate reminders were created for the standup
# (Penalty check - verify agent didn't create bi-weekly=2 standup entries)
# -------------------------------------------------------------------------
try:
    standup_variants = [
        r for r in added_reminders
        if "standup" in r.get("title", "").lower() or "stand-up" in r.get("title", "").lower()
    ]
    # Also check for date-appended titles like "Bi-weekly engineering standup - 2/10"
    date_appended = [r for r in standup_variants if re.search(r'[-–]\s*\d+[/\-]', r.get("title", ""))]
    no_date_appended = len(date_appended) == 0
    single_entry = len(standup_variants) <= 1

    passed = no_date_appended and single_entry
    checks.append({
        "name": "no_manual_standup_duplicates",
        "passed": passed,
        "detail": f"date-appended standup titles: {date_appended}, total standup entries: {len(standup_variants)}"
    })
    if passed:
        total_score += 0.10
except Exception as e:
    checks.append({"name": "no_manual_standup_duplicates", "passed": False, "detail": str(e)})

# -------------------------------------------------------------------------
# CHECK 7: An edit command was issued (agent must update API doc priority or
# change a reminder's details using --id)
# -------------------------------------------------------------------------
try:
    edit_calls = find_cli_calls_with_command("edit")
    has_edit = len(edit_calls) > 0

    # Edit must include --id
    valid_edit = False
    for c in edit_calls:
        args = c.get("args", [])
        if "--id" in args:
            id_idx = args.index("--id")
            if id_idx + 1 < len(args) and args[id_idx+1]:
                valid_edit = True
                break

    passed = has_edit and valid_edit
    checks.append({
        "name": "edit_called_with_id",
        "passed": passed,
        "detail": f"edit calls: {len(edit_calls)}, valid edit with --id: {valid_edit}, calls: {[c['args'] for c in edit_calls]}"
    })
    if passed:
        total_score += 0.10
except Exception as e:
    checks.append({"name": "edit_called_with_id", "passed": False, "detail": str(e)})

# -------------------------------------------------------------------------
# CHECK 8: Output summary file reminder_summary.json exists and has content
# -------------------------------------------------------------------------
try:
    summary_files = list(workspace.rglob("reminder_summary.json"))
    if not summary_files:
        checks.append({"name": "reminder_summary_json_exists", "passed": False, "detail": "reminder_summary.json not found anywhere in workspace"})
    else:
        summary_path = summary_files[0]
        summary = load_json(summary_path)

        # Must contain some list or dict with reminders info
        has_content = False
        if isinstance(summary, list) and len(summary) >= 3:
            has_content = True
        elif isinstance(summary, dict):
            # Could be {"reminders": [...], ...}
            for v in summary.values():
                if isinstance(v, list) and len(v) >= 3:
                    has_content = True
                    break
            if not has_content and len(summary) >= 3:
                has_content = True

        checks.append({
            "name": "reminder_summary_json_exists",
            "passed": has_content,
            "detail": f"Found at {summary_path}, content valid: {has_content}, type: {type(summary).__name__}, len: {len(summary) if isinstance(summary, (list, dict)) else 'N/A'}"
        })
        if has_content:
            total_score += 0.10
except Exception as e:
    checks.append({"name": "reminder_summary_json_exists", "passed": False, "detail": str(e)})

# -------------------------------------------------------------------------
# FINAL SCORING
# -------------------------------------------------------------------------
# Cap score at 1.0
total_score = min(1.0, round(total_score, 3))
overall_passed = (
    any(c["name"] == "parse_called_with_file" and c["passed"] for c in checks) and
    any(c["name"] == "all_four_items_added" and c["passed"] for c in checks) and
    any(c["name"] == "biweekly_standup_uses_repeat_interval2" and c["passed"] for c in checks) and
    any(c["name"] == "no_manual_standup_duplicates" and c["passed"] for c in checks)
)

result = {
    "passed": overall_passed,
    "score": total_score,
    "checks": checks
}

print(json.dumps(result, indent=2, ensure_ascii=False))