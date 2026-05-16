#!/usr/bin/env python3
"""
Evaluation script for the PR Gate Health Audit task.
Usage: python3 eval_script.py /workspace
"""
import json
import sys
import os
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})

# ─── Locate the output file ───────────────────────────────────────────────────
candidates = list(workspace.rglob("gate_audit_report.json"))
if not candidates:
    add_check("output_file_exists", False, "gate_audit_report.json not found anywhere in workspace")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

report_path = candidates[0]
add_check("output_file_exists", True, f"Found at {report_path}")

# ─── Parse JSON ───────────────────────────────────────────────────────────────
try:
    report = json.loads(report_path.read_text())
except Exception as e:
    add_check("json_parseable", False, f"Failed to parse JSON: {e}")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

add_check("json_parseable", True, "Report is valid JSON")

# ─── Check 1: JSON output format (has summary + groups + critical_details) ────
has_summary = isinstance(report.get("summary"), dict)
has_groups  = isinstance(report.get("groups"), list)
has_crit    = isinstance(report.get("critical_details"), list)
ok = has_summary and has_groups and has_crit
add_check(
    "json_output_structure",
    ok,
    f"summary={has_summary}, groups={has_groups}, critical_details={has_crit}"
)

if not ok:
    print(json.dumps({"passed": False, "score": 0.1, "checks": checks}))
    sys.exit(0)

groups = report["groups"]
summary = report["summary"]
critical_details = report["critical_details"]

# ─── Check 2: push events are excluded ────────────────────────────────────────
push_leak = [g for g in groups if g.get("event") == "push"]
add_check(
    "push_events_excluded",
    len(push_leak) == 0,
    f"Groups with event=push found: {[g.get('workflow') for g in push_leak]}"
)

# ─── Check 3: Legacy Smoke workflow is excluded ────────────────────────────────
legacy_leak = [g for g in groups if "Legacy Smoke" in g.get("workflow", "")]
add_check(
    "legacy_smoke_excluded",
    len(legacy_leak) == 0,
    f"Legacy Smoke groups found in output: {legacy_leak}"
)

# ─── Check 4: Groups with < MIN_RUNS=3 are excluded ──────────────────────────
# Infra Validate (1 run), Notify Gate (2 runs), Auth Gate has exactly 3 → OK
under_min = [g for g in groups
             if g.get("workflow") in ("Infra Validate", "Notify Gate")]
add_check(
    "min_runs_filtering_applied",
    len(under_min) == 0,
    f"Groups that should be excluded by MIN_RUNS=3: {[g.get('workflow') for g in under_min]}"
)

# ─── Check 5: Transaction CI (payments/core) is CRITICAL ─────────────────────
txn_groups = [g for g in groups
              if g.get("repo") == "payments/core"
              and g.get("workflow") == "Transaction CI"]
txn_ok = len(txn_groups) > 0 and txn_groups[0].get("level") == "critical"
add_check(
    "transaction_ci_is_critical",
    txn_ok,
    f"Transaction CI group: {txn_groups[0] if txn_groups else 'NOT FOUND'}"
)

# ─── Check 6: Integration Tests (payments/core) is CRITICAL ──────────────────
integ_groups = [g for g in groups
                if g.get("repo") == "payments/core"
                and g.get("workflow") == "Integration Tests"]
integ_ok = len(integ_groups) > 0 and integ_groups[0].get("level") == "critical"
add_check(
    "integration_tests_is_critical",
    integ_ok,
    f"Integration Tests group: {integ_groups[0] if integ_groups else 'NOT FOUND'}"
)

# ─── Check 7: Fraud Gate is present (warning or ok, but must exist) ───────────
fraud_groups = [g for g in groups if g.get("workflow") == "Fraud Gate"]
add_check(
    "fraud_gate_present",
    len(fraud_groups) > 0,
    f"Fraud Gate groups found: {fraud_groups}"
)

# ─── Check 8: Report Build is present and not critical ───────────────────────
report_build = [g for g in groups if g.get("workflow") == "Report Build"]
rb_ok = len(report_build) > 0 and report_build[0].get("level") != "critical"
add_check(
    "report_build_not_critical",
    rb_ok,
    f"Report Build group: {report_build[0] if report_build else 'NOT FOUND'}"
)

# ─── Check 9: Summary counts are consistent ──────────────────────────────────
crit_count = sum(1 for g in groups if g.get("level") == "critical")
warn_count = sum(1 for g in groups if g.get("level") == "warning")
ok_count   = sum(1 for g in groups if g.get("level") == "ok")
summary_consistent = (
    summary.get("critical") == crit_count and
    summary.get("warning")  == warn_count and
    summary.get("ok")       == ok_count
)
add_check(
    "summary_counts_consistent",
    summary_consistent,
    f"Expected crit={crit_count} warn={warn_count} ok={ok_count}; "
    f"Got crit={summary.get('critical')} warn={summary.get('warning')} ok={summary.get('ok')}"
)

# ─── Check 10: critical_details only contains critical groups ─────────────────
bad_crit = [g for g in critical_details if g.get("level") != "critical"]
add_check(
    "critical_details_only_critical",
    len(bad_crit) == 0,
    f"Non-critical entries in critical_details: {bad_crit}"
)

# ─── Check 11: Auth Gate (3 runs, all success) is present and ok ─────────────
auth_groups = [g for g in groups if g.get("workflow") == "Auth Gate"]
auth_ok = len(auth_groups) > 0 and auth_groups[0].get("level") == "ok"
add_check(
    "auth_gate_is_ok",
    auth_ok,
    f"Auth Gate group: {auth_groups[0] if auth_groups else 'NOT FOUND'}"
)

# ─── Check 12: queue scoring applied (Transaction CI avg_queue ~350s) ─────────
if txn_groups:
    q = txn_groups[0].get("avg_queue_seconds", 0)
    queue_scored = q > 300  # above QUEUE_CRITICAL_SECONDS default but we set custom
    add_check(
        "queue_wait_scoring_applied",
        queue_scored,
        f"Transaction CI avg_queue_seconds={q} (expected >300)"
    )
else:
    add_check("queue_wait_scoring_applied", False, "Transaction CI not found")

# ─── Check 13: stale success detection (Transaction CI days_since > 3) ────────
if txn_groups:
    ds = txn_groups[0].get("days_since_last_success", 0)
    stale_ok = ds >= 3.0
    add_check(
        "stale_success_detection",
        stale_ok,
        f"Transaction CI days_since_last_success={ds} (expected >=3)"
    )
else:
    add_check("stale_success_detection", False, "Transaction CI not found")

# ─── Final scoring ─────────────────────────────────────────────────────────────
passed_checks = [c for c in checks if c["passed"]]
score = len(passed_checks) / len(checks)
all_passed = score == 1.0

print(json.dumps({
    "passed": all_passed,
    "score": round(score, 4),
    "checks": checks
}, indent=2))