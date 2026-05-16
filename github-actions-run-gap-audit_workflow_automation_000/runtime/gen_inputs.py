#!/usr/bin/env python3
"""
Generate a realistic fintech CI workspace with GitHub Actions run JSON exports
and a deeply nested distractor file structure.
"""
import json
import os
import random
from datetime import datetime, timezone, timedelta
from pathlib import Path

random.seed(42)

WORKSPACE = os.environ.get("WORKSPACE", "/workspace")

# ── Directory skeleton ────────────────────────────────────────────────────────
dirs = [
    "artifacts/github-actions",
    "skills/github-actions-run-gap-audit/scripts",
    "skills/github-actions-run-gap-audit/fixtures",
    "config/ci",
    "config/compliance",
    "reports/archive/2024",
    "reports/archive/2025",
    "logs/deploys",
    "logs/tests",
    "pipelines/definitions",
    "pipelines/templates",
    "docs/runbooks",
    "scripts/maintenance",
    ".github/workflows",
]
for d in dirs:
    Path(WORKSPACE, d).mkdir(parents=True, exist_ok=True)

# ── Create the required skill script ─────────────────────────────────────────
skill_script = Path(WORKSPACE, "skills/github-actions-run-gap-audit/scripts/run-gap-audit.sh")
skill_script.write_text(
    "#!/usr/bin/env bash\n"
    "# run-gap-audit.sh - GitHub Actions run gap audit script\n"
    "set -euo pipefail\n\n"
    "WORKSPACE=\"${WORKSPACE:-/workspace}\"\n"
    "ARTIFACTS_DIR=\"${ARTIFACTS_DIR:-$WORKSPACE/artifacts/github-actions}\"\n"
    "WARN_GAP_MULTIPLIER=\"${WARN_GAP_MULTIPLIER:-1.5}\"\n"
    "CRITICAL_GAP_MULTIPLIER=\"${CRITICAL_GAP_MULTIPLIER:-2.5}\"\n"
    "MIN_RUNS=\"${MIN_RUNS:-4}\"\n"
    "MIN_CRITICAL_GAP_HOURS=\"${MIN_CRITICAL_GAP_HOURS:-24}\"\n"
    "WORKFLOW_EXCLUDE=\"${WORKFLOW_EXCLUDE:-}\"\n"
    "BRANCH_EXCLUDE=\"${BRANCH_EXCLUDE:-}\"\n"
    "EVENT_EXCLUDE=\"${EVENT_EXCLUDE:-}\"\n\n"
    "echo \"[run-gap-audit] Starting gap audit...\"\n"
    "echo \"[run-gap-audit] Artifacts dir: $ARTIFACTS_DIR\"\n"
)
skill_script.chmod(0o755)

# ── Distractor files ──────────────────────────────────────────────────────────
distractors = {
    "config/ci/pipeline_config.yaml": "version: 2\ntriggers:\n  - push\n  - schedule\n",
    "config/compliance/sox_rules.json": json.dumps({"rules": ["rule-A", "rule-B"], "version": "3.1"}),
    "reports/archive/2024/q4_summary.txt": "Q4 2024 CI health: 98% pass rate\n",
    "reports/archive/2025/q1_summary.txt": "Q1 2025 CI health: 97.2% pass rate\n",
    "logs/deploys/deploy_2025_01.log": "2025-01-15 14:22:01 INFO deployment succeeded\n",
    "logs/tests/unit_test_run_2025.log": "PASSED 1402 tests\nFAILED 3 tests\n",
    "pipelines/definitions/deploy.yml": "name: deploy\non: [push]\njobs:\n  build:\n    runs-on: ubuntu-latest\n",
    "pipelines/templates/reusable_workflow.yml": "on:\n  workflow_call:\njobs:\n  lint:\n    runs-on: ubuntu-latest\n",
    "docs/runbooks/incident_response.md": "# Incident Response\nSee JIRA for escalation paths.\n",
    "scripts/maintenance/rotate_secrets.sh": "#!/bin/bash\necho 'rotating secrets'\n",
    ".github/workflows/codeql.yml": "name: CodeQL\non:\n  schedule:\n    - cron: '0 0 * * 1'\n",
    "config/ci/thresholds.json": json.dumps({"warn_hours": 12, "critical_hours": 24}),
}
for path, content in distractors.items():
    Path(WORKSPACE, path).write_text(content)

# ── NOW reference (fixed for determinism) ────────────────────────────────────
NOW = datetime(2026, 3, 15, 12, 0, 0, tzinfo=timezone.utc)


def iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def make_run(run_id: int, repo: str, workflow: str, branch: str, event: str,
             created_at: datetime, url_suffix: str = "") -> dict:
    url = f"https://github.com/{repo}/actions/runs/{run_id}{url_suffix}"
    started = created_at + timedelta(seconds=random.randint(5, 30))
    updated = started + timedelta(minutes=random.randint(2, 15))
    return {
        "databaseId": run_id,
        "workflowName": workflow,
        "event": event,
        "conclusion": "success",
        "headBranch": branch,
        "headSha": f"abc{run_id:04d}def",
        "createdAt": iso(created_at),
        "startedAt": iso(started),
        "updatedAt": iso(updated),
        "url": url,
        "repository": {"nameWithOwner": repo},
    }


# ──────────────────────────────────────────────────────────────────────────────
# GROUP A: "compliance-check / main / schedule"
#   Healthy cadence ~24h, last run 25h ago → gap=25h, median~24h
#   25 > 24 * 2.5 = 60? NO  → should be OK with default multipliers
#   But with WARN_GAP_MULTIPLIER=1.5: 25 > 24*1.5=36? NO → still OK
#   We'll make it clearly CRITICAL with our custom multipliers:
#   We'll use WARN=1.5, CRITICAL=2.5
#   Gap = 90h, median = 24h → 90 > 24*2.5=60 ✓ AND 90 > 24h ✓ → CRITICAL
# ──────────────────────────────────────────────────────────────────────────────
group_a_runs = []
base_a = NOW - timedelta(hours=90)  # last run was 90h ago
for i in range(8):
    t = base_a - timedelta(hours=24 * (8 - i))
    group_a_runs.append(make_run(
        run_id=10000 + i,
        repo="fintech-org/compliance-engine",
        workflow="compliance-check",
        branch="main",
        event="schedule",
        created_at=t,
    ))
# Add the "last run" 90h ago
group_a_runs.append(make_run(
    run_id=10009,
    repo="fintech-org/compliance-engine",
    workflow="compliance-check",
    branch="main",
    event="schedule",
    created_at=base_a,
))

# ──────────────────────────────────────────────────────────────────────────────
# GROUP B: "deploy-prod / release / push"
#   Cadence ~6h, last run 20h ago → gap=20h, median=6h
#   20 > 6*2.5=15 ✓ AND 20 > 24? NO → WARN (not critical because 20 < MIN_CRITICAL_GAP_HOURS=24)
#   Wait: with MIN_CRITICAL_GAP_HOURS=24 → gap must also be > 24 for critical
#   20 < 24 → WARN only
#   20 > 6*1.5=9 ✓ AND 20 > 12 ✓ → WARN
# ──────────────────────────────────────────────────────────────────────────────
group_b_runs = []
base_b = NOW - timedelta(hours=20)
for i in range(9):
    t = base_b - timedelta(hours=6 * (9 - i))
    group_b_runs.append(make_run(
        run_id=20000 + i,
        repo="fintech-org/payment-service",
        workflow="deploy-prod",
        branch="release",
        event="push",
        created_at=t,
    ))
group_b_runs.append(make_run(
    run_id=20009,
    repo="fintech-org/payment-service",
    workflow="deploy-prod",
    branch="release",
    event="push",
    created_at=base_b,
))

# ──────────────────────────────────────────────────────────────────────────────
# GROUP C: "security-scan / main / push"  ← EXCLUDED by WORKFLOW_EXCLUDE=security
# ──────────────────────────────────────────────────────────────────────────────
group_c_runs = []
base_c = NOW - timedelta(hours=100)
for i in range(6):
    t = base_c - timedelta(hours=12 * (6 - i))
    group_c_runs.append(make_run(
        run_id=30000 + i,
        repo="fintech-org/api-gateway",
        workflow="security-scan",
        branch="main",
        event="push",
        created_at=t,
    ))
group_c_runs.append(make_run(
    run_id=30006,
    repo="fintech-org/api-gateway",
    workflow="security-scan",
    branch="main",
    event="push",
    created_at=base_c,
))

# ──────────────────────────────────────────────────────────────────────────────
# GROUP D: "unit-tests / feature-xyz / push"  ← BRANCH_EXCLUDE=feature.*
# ──────────────────────────────────────────────────────────────────────────────
group_d_runs = []
base_d = NOW - timedelta(hours=80)
for i in range(5):
    t = base_d - timedelta(hours=8 * (5 - i))
    group_d_runs.append(make_run(
        run_id=40000 + i,
        repo="fintech-org/compliance-engine",
        workflow="unit-tests",
        branch="feature-xyz",
        event="push",
        created_at=t,
    ))
group_d_runs.append(make_run(
    run_id=40005,
    repo="fintech-org/compliance-engine",
    workflow="unit-tests",
    branch="feature-xyz",
    event="push",
    created_at=base_d,
))

# ──────────────────────────────────────────────────────────────────────────────
# GROUP E: "integration-tests / main / workflow_dispatch" ← EVENT_EXCLUDE=workflow_dispatch
# ──────────────────────────────────────────────────────────────────────────────
group_e_runs = []
base_e = NOW - timedelta(hours=72)
for i in range(5):
    t = base_e - timedelta(hours=24 * (5 - i))
    group_e_runs.append(make_run(
        run_id=50000 + i,
        repo="fintech-org/payment-service",
        workflow="integration-tests",
        branch="main",
        event="workflow_dispatch",
        created_at=t,
    ))
group_e_runs.append(make_run(
    run_id=50005,
    repo="fintech-org/payment-service",
    workflow="integration-tests",
    branch="main",
    event="workflow_dispatch",
    created_at=base_e,
))

# ──────────────────────────────────────────────────────────────────────────────
# GROUP F: "lint / main / push" — only 3 runs → below MIN_RUNS=4, excluded
# ──────────────────────────────────────────────────────────────────────────────
group_f_runs = []
base_f = NOW - timedelta(hours=50)
for i in range(3):
    t = base_f - timedelta(hours=10 * (3 - i))
    group_f_runs.append(make_run(
        run_id=60000 + i,
        repo="fintech-org/api-gateway",
        workflow="lint",
        branch="main",
        event="push",
        created_at=t,
    ))

# ──────────────────────────────────────────────────────────────────────────────
# GROUP G: "audit-report / main / schedule" — healthy, OK
#   Cadence ~48h, last run 50h ago → gap=50h
#   50 > 48*1.5=72? NO → OK
# ──────────────────────────────────────────────────────────────────────────────
group_g_runs = []
base_g = NOW - timedelta(hours=50)
for i in range(6):
    t = base_g - timedelta(hours=48 * (6 - i))
    group_g_runs.append(make_run(
        run_id=70000 + i,
        repo="fintech-org/compliance-engine",
        workflow="audit-report",
        branch="main",
        event="schedule",
        created_at=t,
    ))
group_g_runs.append(make_run(
    run_id=70006,
    repo="fintech-org/compliance-engine",
    workflow="audit-report",
    branch="main",
    event="schedule",
    created_at=base_g,
))

# ──────────────────────────────────────────────────────────────────────────────
# Write individual run JSON files (one per run, as gh CLI would produce)
# ──────────────────────────────────────────────────────────────────────────────
all_runs = (group_a_runs + group_b_runs + group_c_runs +
            group_d_runs + group_e_runs + group_f_runs + group_g_runs)

out_dir = Path(WORKSPACE, "artifacts/github-actions")
for run in all_runs:
    fname = f"run-{run['databaseId']}.json"
    (out_dir / fname).write_text(json.dumps(run, indent=2))

print(f"[gen_inputs] Written {len(all_runs)} run JSON files to {out_dir}")

# Write a manifest for reference (not a hint, just metadata)
manifest = {
    "generated_at": iso(NOW),
    "total_files": len(all_runs),
    "note": "raw github actions run exports",
}
Path(WORKSPACE, "artifacts/github-actions/MANIFEST.json").write_text(
    json.dumps(manifest, indent=2)
)

# Extra distractor: a stale CSV in reports
Path(WORKSPACE, "reports/archive/2025/pipeline_export.csv").write_text(
    "run_id,workflow,status\n12345,deploy-prod,success\n12346,lint,failure\n"
)

# A fake partial JSON that looks like a run but is malformed
Path(WORKSPACE, "artifacts/github-actions/run-corrupt.json").write_text(
    '{"databaseId": 99999, "workflowName": "broken", "event": "push"'  # truncated
)

print("[gen_inputs] Done.")