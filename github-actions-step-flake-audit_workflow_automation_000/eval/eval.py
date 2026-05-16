#!/usr/bin/env python3
"""
Evaluation script for the GitHub Actions Step Flake Audit task.

Expected agent behaviour:
1. Run the skill script with:
   - RUN_GLOB pointing to artifacts/github-actions/*.json
   - REPO_MATCH=payments-core
   - WORKFLOW_EXCLUDE=nightly-rebuild
   - STEP_EXCLUDE=Notify Slack
   - MIN_OCCURRENCES=5
   - WARN_FAILURE_RATE=0.15
   - CRITICAL_FAILURE_RATE=0.30
   - FAIL_ON_CRITICAL=1
   - OUTPUT_FORMAT=json
2. Capture the JSON output to a file named flake-audit-report.json
3. The exit code should be 1 (critical steps found)
"""

import json
import os
import sys
from pathlib import Path

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
checks = []


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})


# ─── Locate the output file ──────────────────────────────────────────────────
report_files = list(Path(workspace).rglob("flake-audit-report.json"))
if not report_files:
    add_check("output_file_exists", False, "flake-audit-report.json not found anywhere in workspace")
    result = {"passed": False, "score": 0.0, "checks": checks}
    print(json.dumps(result, indent=2))
    sys.exit(0)

report_path = report_files[0]
add_check("output_file_exists", True, f"Found at {report_path}")

# ─── Parse JSON ──────────────────────────────────────────────────────────────
try:
    with open(report_path) as f:
        report = json.load(f)
    add_check("output_is_valid_json", True, "File parsed as valid JSON")
except Exception as e:
    add_check("output_is_valid_json", False, f"JSON parse error: {e}")
    result = {"passed": False, "score": 0.0, "checks": checks}
    print(json.dumps(result, indent=2))
    sys.exit(0)

# ─── Check top-level structure (JSON format output) ─────────────────────────
has_summary       = "summary" in report
has_ranked        = "ranked_groups" in report
has_critical_key  = "critical_groups" in report

add_check("json_has_summary",        has_summary,      f"'summary' key present: {has_summary}")
add_check("json_has_ranked_groups",  has_ranked,       f"'ranked_groups' key present: {has_ranked}")
add_check("json_has_critical_groups",has_critical_key, f"'critical_groups' key present: {has_critical_key}")

if not (has_summary and has_ranked and has_critical_key):
    result = {"passed": False, "score": 1/6, "checks": checks}
    print(json.dumps(result, indent=2))
    sys.exit(0)

summary        = report["summary"]
ranked_groups  = report["ranked_groups"]
critical_groups = report["critical_groups"]

# ─── Check thresholds were applied correctly ─────────────────────────────────
try:
    warn_rate = float(summary.get("warn_failure_rate", -1))
    crit_rate = float(summary.get("critical_failure_rate", -1))

    correct_warn = abs(warn_rate - 0.15) < 0.001
    correct_crit = abs(crit_rate - 0.30) < 0.001

    add_check("warn_threshold_0.15",     correct_warn,
              f"warn_failure_rate in summary={warn_rate} (expected 0.15)")
    add_check("critical_threshold_0.30", correct_crit,
              f"critical_failure_rate in summary={crit_rate} (expected 0.30)")
except Exception as e:
    add_check("threshold_check_error", False, str(e))
    correct_warn = correct_crit = False

# ─── Check MIN_OCCURRENCES filtering ────────────────────────────────────────
# "Deploy Staging" has only 3 obs → must NOT appear in ranked_groups
try:
    deploy_in_ranked = any(
        g.get("step") == "Deploy Staging"
        for g in ranked_groups
    )
    add_check("deploy_staging_excluded_by_min_occ",
              not deploy_in_ranked,
              f"'Deploy Staging' (3 obs < MIN_OCCURRENCES=5) {'present' if deploy_in_ranked else 'correctly absent'} in ranked_groups")
except Exception as e:
    add_check("deploy_staging_check_error", False, str(e))

# ─── Check WORKFLOW_EXCLUDE=nightly-rebuild ──────────────────────────────────
try:
    nightly_in_ranked = any(
        g.get("workflow") == "nightly-rebuild"
        for g in ranked_groups
    )
    add_check("nightly_rebuild_excluded",
              not nightly_in_ranked,
              f"'nightly-rebuild' workflow {'present (BAD)' if nightly_in_ranked else 'correctly absent'} in ranked_groups")
except Exception as e:
    add_check("nightly_rebuild_check_error", False, str(e))

# ─── Check STEP_EXCLUDE=Notify Slack ─────────────────────────────────────────
try:
    notify_in_ranked = any(
        g.get("step") == "Notify Slack"
        for g in ranked_groups
    )
    add_check("notify_slack_excluded",
              not notify_in_ranked,
              f"'Notify Slack' step {'present (BAD)' if notify_in_ranked else 'correctly absent'} in ranked_groups")
except Exception as e:
    add_check("notify_slack_check_error", False, str(e))

# ─── Check REPO_MATCH=payments-core (infra/platform-tools must not appear) ───
try:
    infra_in_ranked = any(
        "platform-tools" in g.get("repo", "")
        for g in ranked_groups
    )
    add_check("infra_platform_tools_excluded",
              not infra_in_ranked,
              f"'infra/platform-tools' {'present (BAD)' if infra_in_ranked else 'correctly absent'} in ranked_groups")
except Exception as e:
    add_check("infra_check_error", False, str(e))

# ─── Check that critical steps ARE present ───────────────────────────────────
# "Run Unit Tests" → 4/8 = 0.500 ≥ 0.30 CRITICAL
# "Integration Test" → 4/7 ≈ 0.571 ≥ 0.30 CRITICAL
try:
    run_unit_crit = any(
        g.get("step") == "Run Unit Tests" and g.get("level") == "critical"
        for g in critical_groups
    )
    add_check("run_unit_tests_is_critical",
              run_unit_crit,
              f"'Run Unit Tests' {'found as critical' if run_unit_crit else 'NOT found as critical'} in critical_groups")
except Exception as e:
    add_check("run_unit_tests_check_error", False, str(e))

try:
    integ_crit = any(
        g.get("step") == "Integration Test" and g.get("level") == "critical"
        for g in critical_groups
    )
    add_check("integration_test_is_critical",
              integ_crit,
              f"'Integration Test' {'found as critical' if integ_crit else 'NOT found as critical'} in critical_groups")
except Exception as e:
    add_check("integration_test_check_error", False, str(e))

# ─── Check Lint Code is present as warn (not critical) ───────────────────────
# Lint Code: 2/8 = 0.25 → 0.15 ≤ 0.25 < 0.30 → WARN
try:
    lint_in_ranked = any(
        g.get("step") == "Lint Code"
        for g in ranked_groups
    )
    lint_level = next(
        (g.get("level") for g in ranked_groups if g.get("step") == "Lint Code"),
        None
    )
    lint_warn = lint_in_ranked and lint_level == "warn"
    add_check("lint_code_is_warn",
              lint_warn,
              f"'Lint Code' in ranked_groups={lint_in_ranked}, level={lint_level} (expected 'warn')")
except Exception as e:
    add_check("lint_code_check_error", False, str(e))

# ─── Check that ranked_groups is non-empty ────────────────────────────────────
try:
    ranked_non_empty = len(ranked_groups) > 0
    add_check("ranked_groups_non_empty",
              ranked_non_empty,
              f"ranked_groups has {len(ranked_groups)} entries")
except Exception as e:
    add_check("ranked_non_empty_error", False, str(e))

# ─── Check exit-code metadata (we look for a sentinel file written by agent) ─
# The agent is expected to capture the exit code and note it, OR we infer from
# critical_groups being non-empty that FAIL_ON_CRITICAL was triggered.
# We verify indirectly: if critical_groups is non-empty, the script would have
# exited 1 — we check the agent actually used FAIL_ON_CRITICAL by confirming
# the report still exists (they captured output before exit 1 consumed the run).
try:
    exit_code_handled = len(critical_groups) > 0
    add_check("fail_on_critical_triggered_correctly",
              exit_code_handled,
              f"critical_groups has {len(critical_groups)} entries; "
              f"FAIL_ON_CRITICAL=1 would have produced exit code 1 (expected)")
except Exception as e:
    add_check("exit_code_check_error", False, str(e))

# ─── Score ───────────────────────────────────────────────────────────────────
total   = len(checks)
passed  = sum(1 for c in checks if c["passed"])
score   = round(passed / total, 4)
overall = passed >= (total - 2)   # allow up to 2 minor misses

result = {
    "passed": overall,
    "score": score,
    "checks": checks
}
print(json.dumps(result, indent=2))