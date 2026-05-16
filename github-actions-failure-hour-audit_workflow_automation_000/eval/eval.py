#!/usr/bin/env python3
"""
Evaluation script for the GitHub Actions Failure Hour Audit task.
Usage: python3 eval.py <workspace_dir>
"""
import sys
import os
import json
import re
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

checks = []
score_parts = []

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    score_parts.append((passed, weight))

# ── Find the output JSON file ──────────────────────────────────────────────────
# Agent is expected to write a JSON report file somewhere in the workspace.
# Accept any file named "failure-audit-report.json" anywhere in the workspace.
report_file = None
try:
    candidates = list(workspace.rglob("failure-audit-report.json"))
    if candidates:
        report_file = candidates[0]
except Exception as e:
    add_check("report_file_found", False, f"Error searching for report: {e}", weight=2.0)

if report_file is None:
    add_check("report_file_found", False, "No 'failure-audit-report.json' found in workspace.", weight=2.0)
else:
    add_check("report_file_found", True, f"Found at {report_file}", weight=2.0)

# ── Parse the JSON report ──────────────────────────────────────────────────────
report = None
if report_file:
    try:
        report = json.loads(report_file.read_text())
        add_check("report_valid_json", True, "Report is valid JSON.", weight=1.0)
    except Exception as e:
        add_check("report_valid_json", False, f"JSON parse error: {e}", weight=1.0)
        report = None

# ── Check top-level keys ───────────────────────────────────────────────────────
if report is not None:
    has_summary = "summary" in report
    has_windows = "windows" in report
    has_critical = "critical_windows" in report
    top_keys_ok = has_summary and has_windows and has_critical
    add_check("report_has_required_keys",
              top_keys_ok,
              f"Keys present: summary={has_summary}, windows={has_windows}, critical_windows={has_critical}",
              weight=1.0)

# ── Validate summary fields ────────────────────────────────────────────────────
if report is not None and "summary" in report:
    s = report["summary"]
    # TZ offset must be 5
    tz_ok = s.get("tz_offset_hours") == 5
    add_check("summary_tz_offset_5",
              tz_ok,
              f"tz_offset_hours in summary = {s.get('tz_offset_hours')} (expected 5)",
              weight=1.5)
    # warn threshold = 3, critical = 5
    warn_ok = s.get("warn_threshold") == 3
    crit_ok = s.get("critical_threshold") == 5
    add_check("summary_thresholds_correct",
              warn_ok and crit_ok,
              f"warn_threshold={s.get('warn_threshold')} (want 3), critical_threshold={s.get('critical_threshold')} (want 5)",
              weight=1.5)

# ── Validate filtering: only trading-engine-ci, no dependabot branches ─────────
# After filtering:
#   - infra-deploy runs excluded (WORKFLOW_MATCH=trading-engine)
#   - dependabot branches excluded (BRANCH_EXCLUDE=dependabot)
#   - success/skipped/neutral excluded (non-failure conclusions)
# Remaining failure runs:
#   UTC 20:xx → local 01:xx Wed : 7 runs  (CRITICAL >= 5)
#   UTC 08:xx → local 13:xx Tue : 4 runs  (WARN >= 3)
#   UTC 03:xx → local 08:xx Tue : 3 runs  (WARN >= 3)
#   UTC 15:xx → local 20:xx Tue : 2 runs  (OK < 3)
# Total failures = 7+4+3+2 = 16

if report is not None and "summary" in report:
    total = report["summary"].get("total_failure_runs")
    total_ok = total == 16
    add_check("summary_total_failure_runs_16",
              total_ok,
              f"total_failure_runs={total} (expected 16 after filtering workflow+branch+conclusion)",
              weight=2.0)

# ── Critical windows must contain Wednesday 01:00 ──────────────────────────────
if report is not None and "critical_windows" in report:
    cw = report["critical_windows"]
    found_critical_window = False
    for w in cw:
        day_ok = str(w.get("day", "")).lower() in ("wednesday", "wed")
        hour_ok = w.get("hour") == 1
        count_ok = w.get("failure_runs", 0) == 7
        if day_ok and hour_ok and count_ok:
            found_critical_window = True
            break
    add_check("critical_window_wednesday_01h_7runs",
              found_critical_window,
              f"Expected critical window: Wednesday 01:00 with 7 failures (TZ+5 shifts UTC 20:xx). critical_windows={json.dumps(cw)}",
              weight=3.0)

# ── Windows array: top window should be Wednesday 01:00 ───────────────────────
if report is not None and "windows" in report:
    wins = report["windows"]
    top_window_correct = False
    if wins:
        w0 = wins[0]
        if (str(w0.get("day", "")).lower() in ("wednesday", "wed")
                and w0.get("hour") == 1
                and w0.get("failure_runs") == 7
                and w0.get("severity") == "critical"):
            top_window_correct = True
    add_check("top_window_is_wednesday_01_critical",
              top_window_correct,
              f"Top window should be Wednesday 01:00 severity=critical 7 runs. Got: {wins[0] if wins else 'empty'}",
              weight=2.0)

# ── Dependabot runs must NOT appear (confirms BRANCH_EXCLUDE worked) ───────────
# If dependabot runs were included, total would be 16+8=24
if report is not None and "summary" in report:
    total = report["summary"].get("total_failure_runs", 0)
    dependabot_excluded = total <= 16
    add_check("dependabot_branches_excluded",
              dependabot_excluded,
              f"total_failure_runs={total}; if >16, dependabot branches were not excluded",
              weight=1.5)

# ── infra-deploy workflow must NOT appear ──────────────────────────────────────
if report is not None and "windows" in report:
    # If infra-deploy included, UTC 20:xx runs add 5 more → Wednesday 01:00 would be 12 (7+5)
    max_win = max((w.get("failure_runs", 0) for w in report["windows"]), default=0)
    infra_excluded = max_win <= 7
    add_check("infra_deploy_workflow_excluded",
              infra_excluded,
              f"Max failure_runs in any window = {max_win}; if >7, infra-deploy was not excluded",
              weight=1.5)

# ── Exit-code file check ───────────────────────────────────────────────────────
# Agent should have checked that the script exits 1 with FAIL_ON_CRITICAL=1
# and recorded this in a file called "audit-exit-code.txt"
exit_code_file = None
try:
    ec_candidates = list(workspace.rglob("audit-exit-code.txt"))
    if ec_candidates:
        exit_code_file = ec_candidates[0]
except Exception:
    pass

if exit_code_file is None:
    add_check("exit_code_file_found", False, "No 'audit-exit-code.txt' found.", weight=1.0)
else:
    try:
        content = exit_code_file.read_text().strip()
        # Accept "1", "exit code: 1", "exit_code=1", etc.
        ec_is_1 = bool(re.search(r'\b1\b', content))
        add_check("exit_code_file_found", True, f"Found at {exit_code_file}", weight=0.5)
        add_check("exit_code_is_1_when_fail_on_critical",
                  ec_is_1,
                  f"Content: '{content}'. Expected to contain '1' (script exits 1 when FAIL_ON_CRITICAL=1 and critical windows exist).",
                  weight=1.0)
    except Exception as e:
        add_check("exit_code_file_found", True, f"Found at {exit_code_file}", weight=0.5)
        add_check("exit_code_is_1_when_fail_on_critical", False, f"Read error: {e}", weight=1.0)

# ── Compute final score ────────────────────────────────────────────────────────
if not score_parts:
    final_score = 0.0
    passed_overall = False
else:
    total_weight = sum(w for _, w in score_parts)
    earned = sum(w for ok, w in score_parts if ok)
    final_score = round(earned / total_weight, 4) if total_weight > 0 else 0.0
    passed_overall = final_score >= 0.75

result = {
    "passed": passed_overall,
    "score": final_score,
    "checks": checks,
}
print(json.dumps(result, indent=2))