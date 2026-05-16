#!/usr/bin/env python3
"""
Evaluation script for the cron-doctor task.

Checks:
1. Report file exists at ~/workspace/reports/cron-health-YYYY-MM-DD.md
2. Report has correct structure (Summary, Failed Jobs, Recommendations sections)
3. Summary counts are present and plausible
4. All 5 failed jobs are documented: sync_trades, db_backup, audit_logins, rotate_keys, daily_pnl
5. Each failed job has an assigned priority that matches SKILL.md priority table:
   - sync_trades  → Critical (trading)
   - db_backup    → Critical (backup)
   - audit_logins → Critical (security)
   - rotate_keys  → Critical (security)
   - daily_pnl    → High (user-facing delivery)
6. Each failed job has the correct error category identified from the SKILL.md error patterns
7. 3+ critical jobs → escalation alert present in the report
8. market_feed is either shown as Healthy or not listed under Failed Jobs
9. weekly_cohort is documented (missing output / not running)
10. Each failed job has a suggested fix
"""

import sys
import json
import re
from pathlib import Path
from datetime import datetime

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/home/agent/workspace")

checks = []

def add_check(name, passed, detail=""):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return passed

# ── 1. Find the report file ─────────────────────────────────────────────────────
report_content = None
report_path = None

try:
    candidates = list((workspace / "reports").glob("cron-health-*.md"))
    if not candidates:
        # Also search recursively in case agent put it in a subdirectory
        candidates = list(workspace.rglob("cron-health-*.md"))
    
    if not candidates:
        add_check("report_file_exists", False,
                  "No file matching 'cron-health-*.md' found under workspace/reports/")
    else:
        # Prefer the most recently modified if multiple
        report_path = sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)[0]
        report_content = report_path.read_text(encoding="utf-8", errors="replace")
        add_check("report_file_exists", True, f"Found: {report_path}")
except Exception as e:
    add_check("report_file_exists", False, f"Exception finding report: {e}")

if report_content is None:
    # No point checking further
    result = {
        "passed": False,
        "score": 0.0,
        "checks": checks
    }
    print(json.dumps(result))
    sys.exit(0)

# Normalise for case-insensitive searching
report_lower = report_content.lower()

# ── 2. Report structural sections ──────────────────────────────────────────────
has_summary = bool(re.search(r'##\s*summary', report_lower))
add_check("section_summary", has_summary,
          "Report must contain a '## Summary' section" if not has_summary else "Found")

has_failed = bool(re.search(r'##\s*failed\s*jobs?', report_lower))
add_check("section_failed_jobs", has_failed,
          "Report must contain a '## Failed Jobs' section" if not has_failed else "Found")

has_recommendations = bool(re.search(r'##\s*recommendations?', report_lower))
add_check("section_recommendations", has_recommendations,
          "Report must contain a '## Recommendations' section" if not has_recommendations else "Found")

# ── 3. Summary counts present ──────────────────────────────────────────────────
# At minimum, look for emoji/keyword indicators of healthy/warning/failed counts
has_counts = bool(re.search(r'(✅|healthy|warning|failed|❌|⚠️)', report_lower))
add_check("summary_has_counts", has_counts,
          "Summary section should include job health counts (healthy/warning/failed)" if not has_counts else "Found count indicators")

# ── 4. Failed jobs documented ──────────────────────────────────────────────────
FAILED_JOBS = {
    "sync_trades": ["sync_trades", "sync trades", "trade sync", "trading/sync"],
    "db_backup": ["db_backup", "db backup", "database backup", "backup/db"],
    "audit_logins": ["audit_logins", "audit logins", "login audit"],
    "rotate_keys": ["rotate_keys", "rotate keys", "key rotation"],
    "daily_pnl": ["daily_pnl", "daily pnl", "pnl report", "daily p&l", "p&l"],
}

for job_key, aliases in FAILED_JOBS.items():
    found = any(alias in report_lower for alias in aliases)
    add_check(f"job_documented_{job_key}", found,
              f"Failed job '{job_key}' must be documented in the report" if not found else f"Found reference to {job_key}")

# ── 5. Priority assignments ─────────────────────────────────────────────────────
# Critical jobs: sync_trades, db_backup, audit_logins, rotate_keys
# High job: daily_pnl
CRITICAL_JOBS = ["sync_trades", "db_backup", "audit_logins", "rotate_keys"]
CRITICAL_ALIASES = {
    "sync_trades": ["sync_trades", "sync trades", "trade sync"],
    "db_backup": ["db_backup", "db backup", "database backup"],
    "audit_logins": ["audit_logins", "audit logins", "login audit"],
    "rotate_keys": ["rotate_keys", "rotate keys", "key rotation"],
}

critical_keyword = re.compile(r'critical', re.IGNORECASE)
high_keyword = re.compile(r'\bhigh\b', re.IGNORECASE)

# Check that "critical" appears in the report at all
has_critical = bool(critical_keyword.search(report_content))
add_check("priority_critical_present", has_critical,
          "Report must assign 'Critical' priority to trading/backup/security jobs" if not has_critical else "Found 'Critical' priority label")

# Check daily_pnl is HIGH (not critical, not medium/low)
pnl_section_match = re.search(
    r'(daily.pnl|pnl.report|daily.p.l|p.l\b)(.*?)(##|\Z)',
    report_lower, re.DOTALL
)
pnl_is_high = False
if pnl_section_match:
    snippet = pnl_section_match.group(2)
    pnl_is_high = bool(re.search(r'\bhigh\b', snippet))
else:
    # Try finding "high" near pnl anywhere in document
    pnl_is_high = bool(re.search(r'(daily.?pnl|pnl|p.?l).{0,200}\bhigh\b|\bhigh\b.{0,200}(daily.?pnl|pnl|p.?l)', report_lower, re.DOTALL))

add_check("priority_daily_pnl_high", pnl_is_high,
          "daily_pnl job must be assigned 'High' priority (user-facing delivery)" if not pnl_is_high else "daily_pnl correctly assigned High priority")

# ── 6. Error patterns identified ───────────────────────────────────────────────
ERROR_CHECKS = [
    ("error_command_not_found", ["command not found"], "sync_trades error 'command not found' must be identified"),
    ("error_permission_denied", ["permission denied"], "db_backup error 'Permission denied' must be identified"),
    ("error_no_such_file", ["no such file", "no such file or directory"], "audit_logins error 'No such file or directory' must be identified"),
    ("error_timeout", ["timeout"], "rotate_keys error 'timeout' must be identified"),
    ("error_econnrefused", ["econnrefused", "connection refused"], "daily_pnl error 'ECONNREFUSED' must be identified"),
]

for check_name, patterns, detail_msg in ERROR_CHECKS:
    found = any(p in report_lower for p in patterns)
    add_check(check_name, found, detail_msg if not found else f"Found: {patterns[0]}")

# ── 7. Escalation alert for 3+ critical failures ───────────────────────────────
# Must contain some escalation/alert language given 4 critical jobs failed
escalation_patterns = [
    r'escalat', r'alert', r'immediate', r'urgent', r'critical.*fail', r'3\+?\s*(or more)?\s*critical',
    r'multiple critical', r'4 critical', r'four critical'
]
has_escalation = any(re.search(p, report_lower) for p in escalation_patterns)
add_check("escalation_alert_present", has_escalation,
          "With 3+ critical job failures, report must include an escalation alert/notice" if not has_escalation
          else "Escalation notice found")

# ── 8. market_feed is healthy (not listed as failed) ──────────────────────────
# Check that market_feed is either not in "Failed Jobs" section or explicitly marked healthy
# We look for "market_feed" in the failed section specifically
failed_section_match = re.search(
    r'##\s*failed\s*jobs?(.*?)(##|\Z)',
    report_lower, re.DOTALL
)
market_feed_in_failed = False
if failed_section_match:
    failed_text = failed_section_match.group(1)
    market_feed_in_failed = bool(re.search(r'market.?feed', failed_text))

add_check("market_feed_not_false_positive", not market_feed_in_failed,
          "market_feed ran successfully and should NOT appear in the Failed Jobs section"
          if market_feed_in_failed else "market_feed correctly excluded from Failed Jobs")

# ── 9. weekly_cohort missing-output noted ─────────────────────────────────────
cohort_noted = bool(re.search(r'weekly.cohort|cohort', report_lower))
add_check("weekly_cohort_documented", cohort_noted,
          "weekly_cohort has no recent execution and should be noted (missing output / not running)"
          if not cohort_noted else "weekly_cohort referenced in report")

# ── 10. Fixes/actions suggested per failed job ────────────────────────────────
fix_keywords = ["fix", "action", "suggest", "recommend", "resolution", "remedy", "path", "chmod", "full path", "backoff", "retry", "directory", "mkdir"]
has_fixes = sum(1 for kw in fix_keywords if kw in report_lower)
add_check("fixes_suggested", has_fixes >= 3,
          f"Expected actionable fixes for failed jobs (found {has_fixes} fix-related keywords)" if has_fixes < 3
          else f"Found {has_fixes} fix-related keywords")

# ── Compute score ──────────────────────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])

# Weighted scoring: structural + escalation checks are more important
WEIGHTS = {
    "report_file_exists": 3,
    "section_summary": 1,
    "section_failed_jobs": 1,
    "section_recommendations": 1,
    "summary_has_counts": 1,
    "job_documented_sync_trades": 2,
    "job_documented_db_backup": 2,
    "job_documented_audit_logins": 2,
    "job_documented_rotate_keys": 2,
    "job_documented_daily_pnl": 2,
    "priority_critical_present": 3,
    "priority_daily_pnl_high": 2,
    "error_command_not_found": 1,
    "error_permission_denied": 1,
    "error_no_such_file": 1,
    "error_timeout": 1,
    "error_econnrefused": 1,
    "escalation_alert_present": 3,
    "market_feed_not_false_positive": 1,
    "weekly_cohort_documented": 1,
    "fixes_suggested": 2,
}

total_weight = sum(WEIGHTS.get(c["name"], 1) for c in checks)
earned_weight = sum(WEIGHTS.get(c["name"], 1) for c in checks if c["passed"])
score = round(earned_weight / total_weight, 4) if total_weight > 0 else 0.0

# Hard gate: must pass report_file_exists and at least escalation + priority checks
hard_gates = ["report_file_exists", "escalation_alert_present", "priority_critical_present"]
hard_passed = all(c["passed"] for c in checks if c["name"] in hard_gates)

overall_passed = hard_passed and score >= 0.70

result = {
    "passed": overall_passed,
    "score": score,
    "checks": checks
}

print(json.dumps(result, ensure_ascii=False, indent=2))