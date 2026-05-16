#!/usr/bin/env python3
"""
Generate a realistic sandbox workspace for the GitHub Actions Manual Trigger Audit task.
Produces messy, real-world-style JSON run files and a deeply nested distractor structure.
"""
import json
import os
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

random.seed(42)

WORKSPACE = os.environ.get("WORKSPACE", "/workspace")

# ── Directory skeleton ────────────────────────────────────────────────────────
dirs = [
    "artifacts/github-actions",
    "artifacts/github-actions/archive/2024",
    "artifacts/github-actions/archive/2023",
    "skills/github-actions-manual-trigger-audit/scripts",
    "skills/github-actions-manual-trigger-audit/fixtures",
    "reports/ci",
    "reports/security",
    "config/thresholds",
    "docs/runbooks",
    "tmp/scratch",
    "logs/audit",
]
for d in dirs:
    Path(WORKSPACE, d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ──────────────────────────────────────────────────────────
distractors = {
    "config/thresholds/slo.yaml": "manual_trigger_warn: 0.40\nmanual_trigger_critical: 0.70\n",
    "config/thresholds/alerts.json": json.dumps({"pagerduty_enabled": True, "slack_channel": "#ci-alerts"}),
    "docs/runbooks/deployment-guide.md": "# Deployment Guide\nSee CI/CD wiki for details.\n",
    "reports/security/cve-scan-2024.csv": "repo,cve,severity\npayments-api,CVE-2024-1234,HIGH\n",
    "logs/audit/previous-run.log": "2024-01-15T10:00:00Z INFO audit completed\n",
    "tmp/scratch/notes.txt": "TODO: check workflow_dispatch usage in release pipeline\n",
    "reports/ci/weekly-summary.txt": "Week 12 CI Summary\nTotal runs: 450\nFailures: 23\n",
    "artifacts/github-actions/archive/2023/old-run-99999.json": json.dumps({
        "databaseId": 99999,
        "workflowName": "Legacy Deploy",
        "event": "workflow_dispatch",
        "headBranch": "master",
        "conclusion": "success",
        "createdAt": "2023-06-01T09:00:00Z",
        "updatedAt": "2023-06-01T09:05:00Z",
        "url": "https://github.com/fintech-org/legacy/actions/runs/99999",
        "repository": {"nameWithOwner": "fintech-org/legacy-service"}
    }),
    "artifacts/github-actions/archive/2024/migrated-run-88888.json": json.dumps({
        "databaseId": 88888,
        "workflowName": "Migrated Pipeline",
        "event": "push",
        "headBranch": "main",
        "conclusion": "success",
        "createdAt": "2024-01-10T08:00:00Z",
        "updatedAt": "2024-01-10T08:10:00Z",
        "url": "https://github.com/fintech-org/migrated/actions/runs/88888",
        "repository": {"nameWithOwner": "fintech-org/migrated-service"}
    }),
    "skills/github-actions-manual-trigger-audit/fixtures/sample.json": json.dumps({
        "databaseId": 1,
        "workflowName": "Sample",
        "event": "push",
        "headBranch": "main",
        "conclusion": "success",
        "createdAt": "2024-03-01T00:00:00Z",
        "updatedAt": "2024-03-01T00:01:00Z",
        "url": "https://github.com/fintech-org/sample/actions/runs/1",
        "repository": {"nameWithOwner": "fintech-org/sample-repo"}
    }),
}
for rel_path, content in distractors.items():
    p = Path(WORKSPACE, rel_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)

# ── Run JSON generation helpers ───────────────────────────────────────────────
BASE_TIME = datetime(2024, 5, 1, 12, 0, 0, tzinfo=timezone.utc)

def make_run(run_id, workflow, event, branch, repo, minutes_ago, conclusion="success"):
    ts = BASE_TIME - timedelta(minutes=minutes_ago)
    ts_str = ts.strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "databaseId": run_id,
        "workflowName": workflow,
        "event": event,
        "headBranch": branch,
        "conclusion": conclusion,
        "createdAt": ts_str,
        "updatedAt": ts_str,
        "url": f"https://github.com/{repo}/actions/runs/{run_id}",
        "repository": {"nameWithOwner": repo}
    }

runs = []
run_id_counter = 10000

def next_id():
    global run_id_counter
    run_id_counter += 1
    return run_id_counter

# ── Repo: fintech-org/payments-api ────────────────────────────────────────────
# Workflow: "Release Deploy" on branch "main"
# 14 runs: 10 workflow_dispatch + 4 push → ratio 10/14 ≈ 0.714 → CRITICAL
# Most recent 5: all workflow_dispatch → streak=5 → CRITICAL streak
repo_pay = "fintech-org/payments-api"
wf_release = "Release Deploy"
for i in range(4):          # older push runs
    runs.append(make_run(next_id(), wf_release, "push", "main", repo_pay, 2000 - i*100))
for i in range(10):         # recent workflow_dispatch runs (newest)
    runs.append(make_run(next_id(), wf_release, "workflow_dispatch", "main", repo_pay, 50 + i*10))

# Workflow: "Release Deploy" on branch "release/2024-q2"
# 6 runs: 3 workflow_dispatch + 3 push → ratio 0.5 → WARN (above 0.35 default)
wf_release_branch = "Release Deploy"
branch_q2 = "release/2024-q2"
for i in range(3):
    runs.append(make_run(next_id(), wf_release_branch, "push", branch_q2, repo_pay, 1500 + i*50))
for i in range(3):
    runs.append(make_run(next_id(), wf_release_branch, "workflow_dispatch", branch_q2, repo_pay, 200 + i*20))

# Workflow: "Unit Tests" on branch "main"
# 20 runs: 1 workflow_dispatch + 19 push → ratio ≈ 0.05 → OK
wf_tests = "Unit Tests"
for i in range(19):
    runs.append(make_run(next_id(), wf_tests, "push", "main", repo_pay, 3000 + i*15))
runs.append(make_run(next_id(), wf_tests, "workflow_dispatch", "main", repo_pay, 30))

# ── Repo: fintech-org/risk-engine ─────────────────────────────────────────────
# Workflow: "Nightly Risk Calc" on branch "main"
# 8 runs: 7 repository_dispatch + 1 schedule → ratio 0.875 → CRITICAL
# Most recent 5: all repository_dispatch → streak=5 → CRITICAL streak
repo_risk = "fintech-org/risk-engine"
wf_nightly = "Nightly Risk Calc"
runs.append(make_run(next_id(), wf_nightly, "schedule", "main", repo_risk, 5000))
for i in range(7):
    runs.append(make_run(next_id(), wf_nightly, "repository_dispatch", "main", repo_risk, 100 + i*12))

# Workflow: "Smoke Test" on branch "main"
# 3 runs total → below MIN_RUNS=5, should be excluded from ranking
wf_smoke = "Smoke Test"
for i in range(2):
    runs.append(make_run(next_id(), wf_smoke, "push", "main", repo_risk, 800 + i*30))
runs.append(make_run(next_id(), wf_smoke, "workflow_dispatch", "main", repo_risk, 10))

# ── Repo: fintech-org/compliance-checker ─────────────────────────────────────
# Workflow: "Compliance Scan" on branch "main"
# 10 runs: 4 workflow_dispatch + 6 push → ratio 0.4 → WARN (above 0.35 default)
# Most recent 5: 2 workflow_dispatch, 3 push → streak=0 (not consecutive at top)
repo_comp = "fintech-org/compliance-checker"
wf_scan = "Compliance Scan"
# Build time-ordered: newest first for streak = 2 non-consecutive
# Newest 5: push, workflow_dispatch, push, workflow_dispatch, push
recent_events = ["push", "workflow_dispatch", "push", "workflow_dispatch", "push"]
for i, ev in enumerate(recent_events):
    runs.append(make_run(next_id(), wf_scan, ev, "main", repo_comp, 20 + i*15))
# Older 5: mix
older_events = ["push", "push", "workflow_dispatch", "push", "workflow_dispatch"]
for i, ev in enumerate(older_events):
    runs.append(make_run(next_id(), wf_scan, ev, "main", repo_comp, 300 + i*30))

# ── Repo: fintech-org/infra-bot (EXCLUDED by WORKFLOW_EXCLUDE) ───────────────
# Workflow: "Infra Provisioner" — should be excluded by regex filter
repo_infra = "fintech-org/infra-bot"
wf_infra = "Infra Provisioner"
for i in range(8):
    runs.append(make_run(next_id(), wf_infra, "workflow_dispatch", "main", repo_infra, 400 + i*20))
for i in range(2):
    runs.append(make_run(next_id(), wf_infra, "push", "main", repo_infra, 200 + i*5))

# ── Repo: external-vendor/third-party-lib (excluded by REPO_MATCH) ───────────
# Should be excluded because REPO_MATCH targets only fintech-org/*
repo_ext = "external-vendor/third-party-lib"
wf_ext = "Build Library"
for i in range(7):
    runs.append(make_run(next_id(), wf_ext, "workflow_dispatch", "main", repo_ext, 500 + i*15))
for i in range(3):
    runs.append(make_run(next_id(), wf_ext, "push", "main", repo_ext, 100 + i*5))

# ── Write all runs to artifacts/github-actions/ ──────────────────────────────
out_dir = Path(WORKSPACE, "artifacts/github-actions")
for run in runs:
    fname = f"run-{run['databaseId']}.json"
    (out_dir / fname).write_text(json.dumps(run, indent=2))

print(f"Generated {len(runs)} run JSON files in {out_dir}")
print("Workspace structure ready.")