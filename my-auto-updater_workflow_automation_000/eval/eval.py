import sys
import os
import json
import re
import subprocess
from pathlib import Path

workspace = sys.argv[1]

checks = []
total_score = 0.0
max_checks = 7  # we'll weight evenly

def make_check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

# ── CHECK 1: setup_autoupdate.sh exists in scripts/maintenance ───────────────
script_path = Path(workspace) / "scripts" / "maintenance" / "setup_autoupdate.sh"
if script_path.exists():
    script_content = script_path.read_text()
    checks.append(make_check(
        "setup_autoupdate.sh exists",
        True,
        f"Found at {script_path}"
    ))
else:
    # Also search anywhere in workspace as fallback
    found = list(Path(workspace).rglob("setup_autoupdate.sh"))
    if found:
        script_path = found[0]
        script_content = script_path.read_text()
        checks.append(make_check(
            "setup_autoupdate.sh exists",
            True,
            f"Found at {script_path} (not in canonical location)"
        ))
    else:
        script_content = ""
        checks.append(make_check(
            "setup_autoupdate.sh exists",
            False,
            "File setup_autoupdate.sh not found anywhere in workspace"
        ))

# ── CHECK 2: Correct cron expression "0 4 * * *" ────────────────────────────
cron_correct = bool(re.search(r'0\s+4\s+\*\s+\*\s+\*', script_content))
checks.append(make_check(
    "Correct cron expression '0 4 * * *'",
    cron_correct,
    f"Found '0 4 * * *' in script: {cron_correct}. Script snippet: {script_content[:300]}"
))

# ── CHECK 3: Required flags --session isolated and --wake now ────────────────
has_session_isolated = bool(re.search(r'--session\s+isolated', script_content))
has_wake_now = bool(re.search(r'--wake\s+now', script_content))
session_wake_ok = has_session_isolated and has_wake_now
checks.append(make_check(
    "Has --session isolated and --wake now flags",
    session_wake_ok,
    f"--session isolated: {has_session_isolated}, --wake now: {has_wake_now}"
))

# ── CHECK 4: --deliver flag present (bare, no value required) ────────────────
has_deliver = bool(re.search(r'--deliver', script_content))
checks.append(make_check(
    "Has --deliver flag",
    has_deliver,
    f"--deliver present: {has_deliver}"
))

# ── CHECK 5: Correct timezone America/Los_Angeles ────────────────────────────
has_tz = bool(re.search(r'America/Los_Angeles', script_content))
checks.append(make_check(
    "Timezone set to America/Los_Angeles",
    has_tz,
    f"America/Los_Angeles found: {has_tz}"
))

# ── CHECK 6: update_summary.md exists and has correct emoji header ───────────
summary_candidates = list(Path(workspace).rglob("update_summary.md"))
if summary_candidates:
    summary_path = summary_candidates[0]
    try:
        summary_content = summary_path.read_text(encoding="utf-8")
    except Exception as e:
        summary_content = ""
        checks.append(make_check(
            "update_summary.md readable",
            False,
            f"Error reading file: {e}"
        ))
else:
    summary_content = ""

summary_exists = bool(summary_content)
checks.append(make_check(
    "update_summary.md exists with content",
    summary_exists,
    f"Found: {bool(summary_candidates)}, path: {summary_candidates[0] if summary_candidates else 'N/A'}"
))

# ── CHECK 7: Summary has correct proprietary format ──────────────────────────
# Must have: 🔄 emoji, version arrows (→), updated skills, already current section
format_checks = {
    "emoji_header": bool(re.search(r'🔄', summary_content)),
    "clawdbot_version_update": bool(re.search(r'v2026\.1\.10.*v2026\.1\.9|v2026\.1\.9.*v2026\.1\.10', summary_content)),
    "arrow_syntax": bool(re.search(r'→', summary_content)),
    "skills_updated_section": bool(re.search(r'Skills Updated', summary_content, re.IGNORECASE)),
    "already_current_section": bool(re.search(r'Already Current|already current', summary_content, re.IGNORECASE)),
    "prd_update": bool(re.search(r'prd.*2\.0\.3.*2\.0\.4|prd.*2\.0\.4', summary_content)),
    "browser_update": bool(re.search(r'browser.*1\.2\.0.*1\.2\.1|browser.*1\.2\.1', summary_content)),
    "nano_banana_update": bool(re.search(r'nano-banana-pro.*3\.1\.0.*3\.1\.2|nano-banana-pro.*3\.1\.2', summary_content)),
    "already_current_names": bool(re.search(r'gemini', summary_content) and re.search(r'sag', summary_content)),
}
format_score = sum(format_checks.values()) / len(format_checks)
format_passed = format_score >= 0.7  # need at least 70% of format checks
checks.append(make_check(
    "update_summary.md has correct proprietary format",
    format_passed,
    f"Format sub-checks: {format_checks}, score: {format_score:.2f}"
))

# ── SCORE CALCULATION ────────────────────────────────────────────────────────
passed_count = sum(1 for c in checks if c["passed"])
score = passed_count / len(checks)
all_passed = all(c["passed"] for c in checks)

# Critical checks: cron expression, session+wake, deliver must all pass for overall pass
critical = [checks[1], checks[2], checks[3]]  # cron, session+wake, deliver
critical_ok = all(c["passed"] for c in critical)

final_passed = all_passed or (critical_ok and score >= 0.75)

result = {
    "passed": final_passed,
    "score": round(score, 3),
    "checks": checks
}

print(json.dumps(result, indent=2, ensure_ascii=False))