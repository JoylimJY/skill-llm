#!/usr/bin/env python3
"""
Generates a realistic sandbox workspace for the github-actions-step-flake-audit task.
Creates:
  - skills/github-actions-step-flake-audit/scripts/step-flake-audit.sh  (the real skill script)
  - artifacts/github-actions/*.json  (10 messy run export files)
  - Distractor files to test contextual awareness
"""

import json
import os
import random
import stat

random.seed(42)

WORKSPACE = os.environ.get("WORKSPACE", "/workspace")


def makedirs(*parts):
    path = os.path.join(WORKSPACE, *parts)
    os.makedirs(path, exist_ok=True)
    return path


# ─── Directory skeleton ──────────────────────────────────────────────────────
makedirs("artifacts", "github-actions")
makedirs("artifacts", "circleci")          # distractor
makedirs("artifacts", "jenkins")           # distractor
makedirs("skills", "github-actions-step-flake-audit", "scripts")
makedirs("skills", "github-actions-step-flake-audit", "fixtures")
makedirs("skills", "github-actions-step-flake-audit", "docs")
makedirs("reports", "old")                 # distractor
makedirs("config")                         # distractor
makedirs("logs")                           # distractor


# ─── Distractor files ────────────────────────────────────────────────────────
distractors = {
    "config/ci-policy.yaml": "retention_days: 30\nmax_parallel_jobs: 8\n",
    "config/thresholds.ini": "[flake]\nwarn=0.25\ncritical=0.50\n",
    "logs/audit-2024-01-10.log": "INFO: previous audit completed\nWARN: 3 steps flagged\n",
    "logs/audit-2024-01-11.log": "INFO: all clear\n",
    "reports/old/summary-q3.txt": "Q3 CI health: 94% pass rate\n",
    "reports/old/summary-q4.txt": "Q4 CI health: 91% pass rate\n",
    "artifacts/circleci/pipeline-1234.json": json.dumps({"pipeline_id": "1234", "status": "success"}),
    "artifacts/jenkins/build-5678.xml": "<build><status>SUCCESS</status></build>",
    "skills/github-actions-step-flake-audit/docs/architecture.md":
        "# Architecture\nThe audit script ingests JSON exported from `gh run view`.\n",
    "skills/github-actions-step-flake-audit/fixtures/sample-run-000.json":
        json.dumps({"databaseId": 0, "workflowName": "sample", "headBranch": "main",
                    "headSha": "abc000", "url": "https://github.com/example/sample/actions/runs/0",
                    "repository": {"nameWithOwner": "example/sample"},
                    "jobs": []}),
}
for rel_path, content in distractors.items():
    full = os.path.join(WORKSPACE, rel_path)
    with open(full, "w") as f:
        f.write(content)


# ─── Build the real skill script ─────────────────────────────────────────────
# This is a faithful implementation of the contract described in SKILL.md
STEP_FLAKE_AUDIT_SH = r'''#!/usr/bin/env bash
# step-flake-audit.sh — GitHub Actions Step Flake Audit (v1.0.0)
set -euo pipefail

RUN_GLOB="${RUN_GLOB:-artifacts/github-actions/*.json}"
TOP_N="${TOP_N:-20}"
OUTPUT_FORMAT="${OUTPUT_FORMAT:-text}"
MIN_OCCURRENCES="${MIN_OCCURRENCES:-3}"
WARN_FAILURE_RATE="${WARN_FAILURE_RATE:-0.20}"
CRITICAL_FAILURE_RATE="${CRITICAL_FAILURE_RATE:-0.40}"
FAIL_ON_CRITICAL="${FAIL_ON_CRITICAL:-0}"
REPO_MATCH="${REPO_MATCH:-}"
REPO_EXCLUDE="${REPO_EXCLUDE:-}"
WORKFLOW_MATCH="${WORKFLOW_MATCH:-}"
WORKFLOW_EXCLUDE="${WORKFLOW_EXCLUDE:-}"
JOB_MATCH="${JOB_MATCH:-}"
JOB_EXCLUDE="${JOB_EXCLUDE:-}"
STEP_MATCH="${STEP_MATCH:-}"
STEP_EXCLUDE="${STEP_EXCLUDE:-}"

python3 "$(dirname "$0")/step-flake-audit.py" \
    --glob        "$RUN_GLOB" \
    --top-n       "$TOP_N" \
    --format      "$OUTPUT_FORMAT" \
    --min-occ     "$MIN_OCCURRENCES" \
    --warn-rate   "$WARN_FAILURE_RATE" \
    --crit-rate   "$CRITICAL_FAILURE_RATE" \
    --fail-crit   "$FAIL_ON_CRITICAL" \
    ${REPO_MATCH:+    --repo-match    "$REPO_MATCH"} \
    ${REPO_EXCLUDE:+  --repo-exclude  "$REPO_EXCLUDE"} \
    ${WORKFLOW_MATCH:+--workflow-match "$WORKFLOW_MATCH"} \
    ${WORKFLOW_EXCLUDE:+--workflow-exclude "$WORKFLOW_EXCLUDE"} \
    ${JOB_MATCH:+     --job-match     "$JOB_MATCH"} \
    ${JOB_EXCLUDE:+   --job-exclude   "$JOB_EXCLUDE"} \
    ${STEP_MATCH:+    --step-match    "$STEP_MATCH"} \
    ${STEP_EXCLUDE:+  --step-exclude  "$STEP_EXCLUDE"}
'''

STEP_FLAKE_AUDIT_PY = r'''#!/usr/bin/env python3
"""step-flake-audit.py — core logic for the GitHub Actions Step Flake Audit skill."""
import argparse
import glob
import json
import re
import sys
from collections import defaultdict

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--glob",         default="artifacts/github-actions/*.json")
    p.add_argument("--top-n",        type=int, default=20)
    p.add_argument("--format",       default="text", choices=["text","json"])
    p.add_argument("--min-occ",      type=int, default=3)
    p.add_argument("--warn-rate",    type=float, default=0.20)
    p.add_argument("--crit-rate",    type=float, default=0.40)
    p.add_argument("--fail-crit",    type=int, default=0)
    p.add_argument("--repo-match",   default="")
    p.add_argument("--repo-exclude", default="")
    p.add_argument("--workflow-match",   default="")
    p.add_argument("--workflow-exclude", default="")
    p.add_argument("--job-match",    default="")
    p.add_argument("--job-exclude",  default="")
    p.add_argument("--step-match",   default="")
    p.add_argument("--step-exclude", default="")
    return p.parse_args()

def match_filter(value, include_pat, exclude_pat):
    if include_pat and not re.search(include_pat, value):
        return False
    if exclude_pat and re.search(exclude_pat, value):
        return False
    return True

def load_runs(pattern):
    files = glob.glob(pattern, recursive=True)
    runs = []
    for f in files:
        try:
            with open(f) as fh:
                runs.append(json.load(fh))
        except Exception:
            pass
    return runs

def collect_outcomes(runs, args):
    # key -> list of conclusions
    groups = defaultdict(list)
    for run in runs:
        repo = run.get("repository", {}).get("nameWithOwner", "unknown/unknown")
        workflow = run.get("workflowName", "unknown")
        if not match_filter(repo, args.repo_match, args.repo_exclude):
            continue
        if not match_filter(workflow, args.workflow_match, args.workflow_exclude):
            continue
        for job in run.get("jobs", []):
            job_name = job.get("name", "unknown")
            if not match_filter(job_name, args.job_match, args.job_exclude):
                continue
            for step in job.get("steps", []):
                step_name = step.get("name", "unknown")
                conclusion = step.get("conclusion", None)
                if conclusion is None:
                    continue
                if not match_filter(step_name, args.step_match, args.step_exclude):
                    continue
                key = (repo, workflow, job_name, step_name)
                groups[key].append(conclusion)
    return groups

def score_groups(groups, args):
    results = []
    for (repo, workflow, job, step), conclusions in groups.items():
        total = len(conclusions)
        if total < args.min_occ:
            continue
        successes = sum(1 for c in conclusions if c in ("success",))
        failures  = sum(1 for c in conclusions if c in ("failure",))
        # Only flaky if BOTH success and failure present
        if successes == 0 or failures == 0:
            continue
        fail_rate = failures / total
        results.append({
            "repo": repo,
            "workflow": workflow,
            "job": job,
            "step": step,
            "total_runs": total,
            "success_count": successes,
            "failure_count": failures,
            "failure_rate": round(fail_rate, 4),
        })
    # rank: by failure_rate desc, then failure_count desc
    results.sort(key=lambda x: (-x["failure_rate"], -x["failure_count"]))
    return results

def classify(entry, warn_rate, crit_rate):
    fr = entry["failure_rate"]
    if fr >= crit_rate:
        return "critical"
    if fr >= warn_rate:
        return "warn"
    return "ok"

def main():
    args = parse_args()
    runs = load_runs(args.glob)
    groups = collect_outcomes(runs, args)
    scored = score_groups(groups, args)
    top = scored[:args.top_n]

    warn_rate = args.warn_rate
    crit_rate = args.crit_rate

    critical_groups = [e for e in top if classify(e, warn_rate, crit_rate) == "critical"]
    warn_groups     = [e for e in top if classify(e, warn_rate, crit_rate) == "warn"]

    summary = {
        "total_files_loaded": len(load_runs(args.glob)),
        "total_step_groups_evaluated": len(scored),
        "critical_count": len(critical_groups),
        "warn_count": len(warn_groups),
        "top_n": args.top_n,
        "min_occurrences": args.min_occ,
        "warn_failure_rate": warn_rate,
        "critical_failure_rate": crit_rate,
    }

    if args.format == "json":
        output = {
            "summary": summary,
            "ranked_groups": [dict(level=classify(e, warn_rate, crit_rate), **e) for e in top],
            "critical_groups": [dict(level="critical", **e) for e in critical_groups],
        }
        print(json.dumps(output, indent=2))
    else:
        print("=== GitHub Actions Step Flake Audit ===")
        print(f"Files loaded       : {summary['total_files_loaded']}")
        print(f"Step groups scored : {summary['total_step_groups_evaluated']}")
        print(f"Critical           : {summary['critical_count']}")
        print(f"Warn               : {summary['warn_count']}")
        print(f"Thresholds         : warn>={warn_rate:.0%}  critical>={crit_rate:.0%}")
        print(f"Min occurrences    : {args.min_occ}")
        print()
        print(f"{'RANK':<5} {'LEVEL':<9} {'FAIL%':<7} {'FAILS':<6} {'TOTAL':<6} STEP")
        print("-" * 80)
        for i, e in enumerate(top, 1):
            level = classify(e, warn_rate, crit_rate)
            print(f"{i:<5} {level:<9} {e['failure_rate']:<7.1%} {e['failure_count']:<6} {e['total_runs']:<6} "
                  f"{e['repo']} / {e['workflow']} / {e['job']} / {e['step']}")

    if args.fail_crit and critical_groups:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
'''

scripts_dir = makedirs("skills", "github-actions-step-flake-audit", "scripts")

sh_path = os.path.join(scripts_dir, "step-flake-audit.sh")
with open(sh_path, "w") as f:
    f.write(STEP_FLAKE_AUDIT_SH)
os.chmod(sh_path, os.stat(sh_path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

py_path = os.path.join(scripts_dir, "step-flake-audit.py")
with open(py_path, "w") as f:
    f.write(STEP_FLAKE_AUDIT_PY)
os.chmod(py_path, os.stat(py_path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


# ─── Generate realistic GitHub Actions run JSON exports ──────────────────────
# We craft data so that:
#   - REPO_MATCH="payments-core" → keeps payments-core/payments-api, payments-core/payment-gateway
#   - REPO_EXCLUDE not set in this task
#   - WORKFLOW_EXCLUDE="nightly-rebuild" → drops nightly-rebuild runs
#   - STEP_EXCLUDE="Notify Slack" → drops Notify Slack steps
#   - MIN_OCCURRENCES=5 → steps must appear ≥5 times
#   - WARN_FAILURE_RATE=0.15 → warn threshold
#   - CRITICAL_FAILURE_RATE=0.30 → critical threshold
#   - FAIL_ON_CRITICAL=1 → exit 1 expected
#
# Key steps designed into data (after filters & thresholds):
#   - "Run Unit Tests"   in payments-api / ci-main: 8 total, 4 fail → 0.500  CRITICAL ✓
#   - "Integration Test" in payment-gateway / ci-main: 7 total, 3 fail → 0.429 CRITICAL ✓
#   - "Lint Code"        in payments-api / ci-main: 6 total, 1 fail → 0.167  WARN ✓
#   - "Notify Slack"     EXCLUDED by STEP_EXCLUDE
#   - "Build Docker"     in nightly-rebuild workflow → EXCLUDED by WORKFLOW_EXCLUDE
#   - Steps in "infra/platform-tools" → EXCLUDED by REPO_MATCH (no payments-core)
#   - "Deploy Staging"   only 3 occurrences → EXCLUDED by MIN_OCCURRENCES=5

REPOS = {
    "payments-core/payments-api": [
        # workflow: ci-main
        # step: Run Unit Tests — 8 runs: 4 success, 4 failure → 0.500 CRITICAL
        # step: Lint Code       — 6 runs: 5 success, 1 failure → 0.167 WARN
        # step: Notify Slack    — 6 runs: all success (but EXCLUDED by STEP_EXCLUDE)
        ("ci-main", "build-and-test", [
            ("Checkout", "success"),
            ("Run Unit Tests", "failure"),
            ("Lint Code", "success"),
            ("Notify Slack", "success"),
        ]),
    ],
    "payments-core/payment-gateway": [
        # workflow: ci-main
        # step: Integration Test — 7 runs: 3 success, 4 failure → 0.571... wait let me recalc
        # Actually: 7 total, 3 fail → 3/7 = 0.429 CRITICAL
        ("ci-main", "integration", [
            ("Checkout", "success"),
            ("Integration Test", "failure"),
            ("Generate Report", "success"),
        ]),
    ],
    "infra/platform-tools": [
        # EXCLUDED by REPO_MATCH=payments-core (no match)
        ("ci-infra", "infra-check", [
            ("Terraform Validate", "failure"),
            ("Terraform Plan", "failure"),
        ]),
    ],
}

# We need to create run files with specific conclusion patterns:
# payments-core/payments-api  ci-main  build-and-test  "Run Unit Tests": 8 obs → conclusions
#   4 success + 4 failure  (8 total, rate=0.500 CRITICAL)
# payments-core/payments-api  ci-main  build-and-test  "Lint Code": 6 obs
#   5 success + 1 failure  (6 total, rate=0.167 WARN)
# payments-core/payments-api  ci-main  build-and-test  "Notify Slack": 6 obs (all success → NOT flaky, no both)
# payments-core/payment-gateway  ci-main  integration  "Integration Test": 7 obs
#   4 success + 3 failure  (7 total, rate=0.429 CRITICAL)
# infra/platform-tools  ci-infra  infra-check  "Terraform Validate": 6 failure only → NOT flaky

# Also add nightly-rebuild workflow (EXCLUDED by WORKFLOW_EXCLUDE):
# payments-core/payments-api  nightly-rebuild  build-and-test  "Build Docker": 6 obs 3+3 → would be CRITICAL but excluded

# Deploy Staging: only 3 occurrences → below MIN_OCCURRENCES=5 → excluded

run_id = 1000

def make_job(job_name, steps_outcomes):
    return {
        "name": job_name,
        "steps": [{"name": s, "conclusion": c} for s, c in steps_outcomes]
    }

def make_run(run_id, repo_full, workflow_name, jobs_data):
    return {
        "databaseId": run_id,
        "workflowName": workflow_name,
        "headBranch": "main",
        "headSha": f"sha{run_id:08x}",
        "url": f"https://github.com/{repo_full}/actions/runs/{run_id}",
        "repository": {"nameWithOwner": repo_full},
        "jobs": jobs_data
    }

# We'll produce one JSON file per run (each run is one invocation).
# Some files will contain multiple repos to simulate monorepo exports.

runs_to_write = []

# ── payments-core/payments-api, ci-main: 8 runs ──────────────────────────────
# Run Unit Tests:  [fail, suc, fail, suc, fail, suc, fail, suc]  → 4/8=0.500 CRITICAL
# Lint Code:       [suc,  suc, suc,  suc, suc,  fail, suc,  suc] → 1/8... 
# Actually we want 6 Lint obs. Let's just make 8 for consistency, 1 fail:
# Lint: [suc, suc, suc, suc, fail, suc, suc, suc] → 1/8=0.125 < 0.15 WARN threshold
# Adjust: Lint [suc, suc, suc, suc, fail, suc, suc, fail] → 2/8=0.25 → but we want exactly WARN (0.15..0.30)
# Let's do 8 runs: 2 fail → 2/8=0.250 WARN ✓
unit_test_outcomes = ["failure","success","failure","success","failure","success","failure","success"]
lint_outcomes      = ["success","success","success","success","failure","success","success","failure"]
notify_slack_out   = ["success","success","success","success","success","success","success","success"]
nightly_docker_out = ["failure","success","failure","success","failure","success","failure","success"]

for i, (ut, lint, ns) in enumerate(zip(unit_test_outcomes, lint_outcomes, notify_slack_out)):
    steps = [
        ("Checkout", "success"),
        ("Run Unit Tests", ut),
        ("Lint Code", lint),
        ("Notify Slack", ns),
    ]
    job = make_job("build-and-test", steps)
    run = make_run(run_id, "payments-core/payments-api", "ci-main", [job])
    runs_to_write.append(run)
    run_id += 1

# ── payments-core/payments-api, nightly-rebuild: 8 runs (WORKFLOW EXCLUDED) ──
for i, docker_out in enumerate(nightly_docker_out):
    steps = [
        ("Checkout", "success"),
        ("Build Docker", docker_out),
        ("Push to Registry", "success"),
    ]
    job = make_job("build-and-test", steps)
    run = make_run(run_id, "payments-core/payments-api", "nightly-rebuild", [job])
    runs_to_write.append(run)
    run_id += 1

# ── payments-core/payment-gateway, ci-main: 7 runs ───────────────────────────
# Integration Test: 4 fail, 3 success → 4/7 ≈ 0.571 CRITICAL
integration_outcomes = ["failure","failure","success","failure","success","failure","success"]
for i, integ in enumerate(integration_outcomes):
    steps = [
        ("Checkout", "success"),
        ("Integration Test", integ),
        ("Generate Report", "success"),
    ]
    job = make_job("integration", steps)
    run = make_run(run_id, "payments-core/payment-gateway", "ci-main", [job])
    runs_to_write.append(run)
    run_id += 1

# ── payments-core/payment-gateway, ci-main: Deploy Staging — only 3 runs ─────
# (below MIN_OCCURRENCES=5, so excluded from scoring)
deploy_outcomes = ["failure", "success", "failure"]
for i, dep in enumerate(deploy_outcomes):
    steps = [
        ("Checkout", "success"),
        ("Deploy Staging", dep),
    ]
    job = make_job("deploy", steps)
    run = make_run(run_id, "payments-core/payment-gateway", "ci-main", [job])
    runs_to_write.append(run)
    run_id += 1

# ── infra/platform-tools, ci-infra: 6 runs (REPO EXCLUDED) ──────────────────
infra_outcomes = ["failure","failure","failure","failure","success","failure"]
for i, infra in enumerate(infra_outcomes):
    steps = [
        ("Terraform Validate", infra),
        ("Terraform Plan", "success"),
    ]
    job = make_job("infra-check", steps)
    run = make_run(run_id, "infra/platform-tools", "ci-infra", [job])
    runs_to_write.append(run)
    run_id += 1

# Write each run to its own file
artifact_dir = os.path.join(WORKSPACE, "artifacts", "github-actions")
for run in runs_to_write:
    filename = f"run-{run['databaseId']}.json"
    with open(os.path.join(artifact_dir, filename), "w") as f:
        json.dump(run, f, indent=2)

print(f"Generated {len(runs_to_write)} run JSON files.")
print("Workspace structure ready.")

# Verify the fixture dir has the sample file
fixture_path = os.path.join(WORKSPACE, "skills/github-actions-step-flake-audit/fixtures/sample-run-000.json")
assert os.path.exists(fixture_path), "fixture missing"
print("All done.")