#!/usr/bin/env python3
"""
Generates a realistic, messy sandbox workspace for the PR gate health audit task.
All randomness is seeded for determinism.
"""
import json
import os
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ─── Directory skeleton (distractors) ────────────────────────────────────────
dirs = [
    "artifacts/github-actions",
    "artifacts/old-exports",
    "artifacts/coverage-reports",
    "logs/ci",
    "logs/deploy",
    "config/thresholds",
    "config/alerts",
    "docs/runbooks",
    "reports/weekly",
    "scripts/helpers",
    "skills/github-actions-pr-gate-health-audit/scripts",
    "skills/github-actions-pr-gate-health-audit/fixtures",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ─── Distractor files ─────────────────────────────────────────────────────────
distractor_files = {
    "docs/runbooks/incident-response.md": "# Incident Response\nSee Confluence for details.",
    "docs/runbooks/on-call.md": "# On-Call Rotation\nPagerDuty handles escalation.",
    "config/thresholds/alerting.yaml": "failure_rate_warn: 0.2\nfailure_rate_crit: 0.5\n",
    "config/alerts/pagerduty.json": json.dumps({"service_key": "REDACTED", "severity": "critical"}),
    "logs/ci/last-run.log": "2024-03-15T10:22:01Z INFO pipeline completed\n",
    "logs/deploy/prod-deploy-20240315.log": "Deploy succeeded in 142s\n",
    "reports/weekly/2024-W10.csv": "repo,workflow,pass_rate\npayments/core,CI,0.91\n",
    "reports/weekly/2024-W11.csv": "repo,workflow,pass_rate\npayments/core,CI,0.88\n",
    "scripts/helpers/notify_slack.sh": "#!/bin/bash\necho 'Slack notification stub'\n",
    "artifacts/old-exports/legacy-run-001.json": json.dumps({"id": 1, "status": "old_format"}),
    "artifacts/coverage-reports/coverage-summary.json": json.dumps({"total": 82.4}),
    "config/thresholds/sla.json": json.dumps({"p99_latency_ms": 500, "error_budget_percent": 0.1}),
}
for path, content in distractor_files.items():
    (WORKSPACE / path).write_text(content)

# ─── Helpers ──────────────────────────────────────────────────────────────────
NOW = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)

def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

def make_run(run_id, repo, workflow, event, conclusion,
             created_offset_days, queue_wait_seconds,
             duration_seconds=120):
    created = NOW - timedelta(days=created_offset_days)
    started = created + timedelta(seconds=queue_wait_seconds)
    updated = started + timedelta(seconds=duration_seconds)
    return {
        "databaseId": run_id,
        "workflowName": workflow,
        "event": event,
        "conclusion": conclusion,
        "headBranch": f"feature/run-{run_id}",
        "headSha": f"{run_id:040x}",
        "createdAt": iso(created),
        "runStartedAt": iso(started),
        "updatedAt": iso(updated),
        "url": f"https://github.com/{repo}/actions/runs/{run_id}",
        "repository": {"nameWithOwner": repo},
    }

# ─── Scenario definitions ─────────────────────────────────────────────────────
# We craft groups with KNOWN scoring outcomes for deterministic eval.

run_id = 1000

runs = []

# ── GROUP A: payments/core  |  "Transaction CI"  |  pull_request
# HIGH failure rate (40%), high queue wait, stale success → CRITICAL
# 10 runs: 4 failures, 6 success; last success = 5 days ago; queue ~350s
for i in range(6):
    days_ago = 5 + i        # successes are 5–10 days old
    runs.append(make_run(run_id, "payments/core", "Transaction CI",
                         "pull_request", "success",
                         days_ago, queue_wait_seconds=350))
    run_id += 1
for i in range(4):
    days_ago = i * 0.5      # failures are recent (0–2 days old)
    runs.append(make_run(run_id, "payments/core", "Transaction CI",
                         "pull_request", "failure",
                         days_ago, queue_wait_seconds=350))
    run_id += 1

# ── GROUP B: payments/fraud-detection  |  "Fraud Gate"  |  merge_group
# MODERATE failure rate (20%), moderate queue (200s), recent success → WARN
for i in range(8):
    conc = "failure" if i < 2 else "success"
    days_ago = i * 0.3
    runs.append(make_run(run_id, "payments/fraud-detection", "Fraud Gate",
                         "merge_group", conc,
                         days_ago, queue_wait_seconds=200))
    run_id += 1

# ── GROUP C: payments/reporting  |  "Report Build"  |  pull_request
# LOW failure rate (10%), low queue (60s), fresh success → HEALTHY
for i in range(10):
    conc = "failure" if i == 0 else "success"
    days_ago = i * 0.2
    runs.append(make_run(run_id, "payments/reporting", "Report Build",
                         "pull_request", conc,
                         days_ago, queue_wait_seconds=60))
    run_id += 1

# ── GROUP D: payments/legacy-batch  |  "Legacy Smoke"  |  pull_request
# This workflow should be EXCLUDED by the agent via WORKFLOW_EXCLUDE regex
# Include failures that would be critical if not excluded
for i in range(6):
    conc = "failure" if i < 4 else "success"
    days_ago = i * 0.1
    runs.append(make_run(run_id, "payments/legacy-batch", "Legacy Smoke",
                         "pull_request", conc,
                         days_ago, queue_wait_seconds=80))
    run_id += 1

# ── GROUP E: payments/core  |  "Security Scan"  |  push  (NOT a PR event)
# Should be filtered out by EVENT_MATCH (push ≠ pull_request|merge_group)
for i in range(5):
    conc = "failure" if i < 3 else "success"
    days_ago = i * 0.5
    runs.append(make_run(run_id, "payments/core", "Security Scan",
                         "push", conc,
                         days_ago, queue_wait_seconds=50))
    run_id += 1

# ── GROUP F: payments/core  |  "Integration Tests"  |  pull_request_target
# CRITICAL: 50% failure rate, very high queue (500s), stale success
for i in range(6):
    conc = "failure" if i < 3 else "success"
    days_ago = 4 + i  # successes are 4–9 days ago
    runs.append(make_run(run_id, "payments/core", "Integration Tests",
                         "pull_request_target", conc,
                         days_ago, queue_wait_seconds=500))
    run_id += 1

# ── GROUP G: infra/platform  |  "Infra Validate"  |  pull_request
# Only 1 run → should be filtered out by MIN_RUNS=3
runs.append(make_run(run_id, "infra/platform", "Infra Validate",
                     "pull_request", "failure", 0.1, queue_wait_seconds=100))
run_id += 1

# ── GROUP H: payments/notifications  |  "Notify Gate"  |  pull_request
# 2 runs (< MIN_RUNS=3) → filtered out
for i in range(2):
    runs.append(make_run(run_id, "payments/notifications", "Notify Gate",
                         "pull_request", "success", i * 0.5, queue_wait_seconds=90))
    run_id += 1

# ── GROUP I: payments/auth  |  "Auth Gate"  |  merge_group
# Exactly 3 runs, 0% failure, fresh success → HEALTHY (just above MIN_RUNS threshold)
for i in range(3):
    runs.append(make_run(run_id, "payments/auth", "Auth Gate",
                         "merge_group", "success", i * 0.2, queue_wait_seconds=80))
    run_id += 1

# ─── Write each run as its own JSON file ──────────────────────────────────────
out_dir = WORKSPACE / "artifacts/github-actions"
for run in runs:
    fname = f"run-{run['databaseId']}.json"
    (out_dir / fname).write_text(json.dumps(run, indent=2))

# ─── Also populate the fixtures dir with a subset (distractor – not what agent should use) ──
fixtures_dir = WORKSPACE / "skills/github-actions-pr-gate-health-audit/fixtures"
for run in runs[:5]:
    fname = f"fixture-run-{run['databaseId']}.json"
    (fixtures_dir / fname).write_text(json.dumps(run, indent=2))

# ─── Write a stub audit-config for distraction ────────────────────────────────
(WORKSPACE / "config/thresholds/audit-config.json").write_text(json.dumps({
    "note": "These values are for the legacy dashboard only. Do not use for CLI invocations.",
    "fail_warn_percent": 10,
    "fail_critical_percent": 25,
    "queue_warn_seconds": 90,
    "queue_critical_seconds": 240,
}, indent=2))

print("Sandbox inputs generated successfully.")
print(f"Total run files: {len(runs)}")