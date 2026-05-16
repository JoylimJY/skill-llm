#!/usr/bin/env python3
"""
Generate the sandbox workspace for the GitHub Actions Runtime Regression Audit task.
Creates:
- Realistic gh run export JSON files (baseline + current) in appropriate directories
- The skill's script at the expected path
- Distractor files to simulate a real repo
"""

import json
import os
import random
import math
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "artifacts/github-actions/baseline",
    "artifacts/github-actions/current",
    "artifacts/github-actions/archive",
    "skills/github-actions-runtime-regression-audit/scripts",
    "skills/github-actions-runtime-regression-audit/fixtures",
    "skills/github-actions-runtime-regression-audit/tests",
    "reports/ci",
    "reports/cost",
    "src/payments",
    "src/ledger",
    "src/auth",
    "infra/terraform",
    "infra/helm",
    ".github/workflows",
    "docs/runbooks",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── distractor files ────────────────────────────────────────────────────────
distractors = {
    "src/payments/processor.py": "# payment processor\ndef charge(amount): pass\n",
    "src/ledger/journal.py": "# ledger\ndef post(entry): pass\n",
    "src/auth/tokens.py": "# auth tokens\ndef validate(tok): pass\n",
    "infra/terraform/main.tf": 'provider "aws" { region = "us-east-1" }\n',
    "infra/helm/values.yaml": "replicaCount: 3\nimage:\n  tag: latest\n",
    ".github/workflows/deploy.yml": "name: Deploy\non: [push]\njobs:\n  deploy:\n    runs-on: ubuntu-latest\n    steps: []\n",
    "docs/runbooks/incident-response.md": "# Incident Response\nSee playbook v2.\n",
    "reports/cost/monthly-summary.csv": "month,spend\n2024-01,12000\n2024-02,13500\n",
    "reports/ci/stale-report.txt": "Generated 2023-12-01. Superseded.\n",
    "artifacts/github-actions/archive/old-run-99999.json": json.dumps({"note": "archived run, do not process"}),
    "skills/github-actions-runtime-regression-audit/tests/test_placeholder.sh": "#!/bin/bash\necho 'unit tests go here'\n",
}
for rel, content in distractors.items():
    p = WORKSPACE / rel
    p.write_text(content)

# ── helper: build a realistic gh-run-view JSON ───────────────────────────────
def make_run_json(
    run_id: int,
    repo_name: str,
    workflow_name: str,
    branch: str,
    sha: str,
    url: str,
    jobs: list[dict],
) -> dict:
    """Mimic output of:  gh run view <id> --json databaseId,workflowName,headBranch,headSha,url,repository,jobs"""
    return {
        "databaseId": run_id,
        "workflowName": workflow_name,
        "headBranch": branch,
        "headSha": sha,
        "url": url,
        "repository": {
            "nameWithOwner": repo_name,
            "name": repo_name.split("/")[-1],
        },
        "jobs": jobs,
    }


def make_job(name: str, duration_seconds: int, conclusion: str = "success") -> dict:
    """Build a single job entry with startedAt / completedAt timestamps."""
    import datetime
    started = datetime.datetime(2024, 3, 1, 10, 0, 0, tzinfo=datetime.timezone.utc)
    completed = started + datetime.timedelta(seconds=duration_seconds)
    return {
        "name": name,
        "conclusion": conclusion,
        "startedAt": started.isoformat(),
        "completedAt": completed.isoformat(),
        "steps": [],
    }


# ── Data design ──────────────────────────────────────────────────────────────
# We define per-job BASELINE durations and CURRENT durations.
# Regressions are carefully calibrated against the CUSTOM thresholds the task will use:
#   WARN_DELTA_SECONDS=60   CRITICAL_DELTA_SECONDS=150
#   WARN_DELTA_PERCENT=20   CRITICAL_DELTA_PERCENT=40
#
# Key cases:
#  A) "build-docker"   (repo: fintech/payments):  baseline ~120s, current ~290s  → +170s, +141% → CRITICAL (both)
#  B) "run-unit-tests" (repo: fintech/payments):  baseline ~200s, current ~270s  → +70s,  +35%  → WARN (seconds only)
#  C) "lint"           (repo: fintech/ledger):    baseline ~80s,  current ~115s  → +35s,  +44%  → WARN (percent breaches 20% but not 40%), seconds breach 60 → WARN
#  D) "integration"    (repo: fintech/ledger):    baseline ~300s, current ~465s  → +165s, +55%  → CRITICAL (both)
#  E) "security-scan"  (repo: fintech/auth):      baseline ~150s, current ~155s  → +5s,   +3%   → no regression (neither threshold breached)
#  F) "deploy-staging" (repo: fintech/auth):      baseline p95 driven by outlier → new interesting case
#  G) "e2e-tests"      (repo: fintech/payments):  brand new job (no baseline)    → "new job without baseline"
#
# We create MULTIPLE baseline runs per job so p95 can differ from average.

REPO_PAYMENTS = "fintech/payments"
REPO_LEDGER   = "fintech/ledger"
REPO_AUTH     = "fintech/auth"

WORKFLOW_CI     = "CI Pipeline"
WORKFLOW_DEPLOY = "Deploy"
WORKFLOW_AUDIT  = "Security Audit"   # will be excluded by JOB_EXCLUDE filter in the task

# Baseline runs: 8 runs per repo, spread across 2 weeks
# We store (job_name, durations_list) per workflow/repo

baseline_runs_payments_ci = [
    # (run_id, [job_durations_dict])
    # job durations in seconds: build-docker, run-unit-tests
    (1001, {"build-docker": 118, "run-unit-tests": 195}),
    (1002, {"build-docker": 122, "run-unit-tests": 198}),
    (1003, {"build-docker": 119, "run-unit-tests": 202}),
    (1004, {"build-docker": 121, "run-unit-tests": 197}),
    (1005, {"build-docker": 125, "run-unit-tests": 205}),
    (1006, {"build-docker": 117, "run-unit-tests": 193}),
    (1007, {"build-docker": 123, "run-unit-tests": 200}),
    (1008, {"build-docker": 120, "run-unit-tests": 199}),
]

baseline_runs_ledger_ci = [
    (2001, {"lint": 78, "integration": 295}),
    (2002, {"lint": 81, "integration": 302}),
    (2003, {"lint": 79, "integration": 298}),
    (2004, {"lint": 82, "integration": 305}),
    (2005, {"lint": 77, "integration": 293}),
    (2006, {"lint": 80, "integration": 300}),
    (2007, {"lint": 83, "integration": 308}),
    (2008, {"lint": 78, "integration": 297}),
]

baseline_runs_auth_audit = [
    # security-scan has a high p95 due to one outlier
    (3001, {"security-scan": 148}),
    (3002, {"security-scan": 152}),
    (3003, {"security-scan": 149}),
    (3004, {"security-scan": 151}),
    (3005, {"security-scan": 147}),
    (3006, {"security-scan": 153}),
    (3007, {"security-scan": 150}),
    (3008, {"security-scan": 400}),  # outlier → raises p95 for baseline
]

# Current runs: 4 runs per repo
current_runs_payments_ci = [
    (5001, {"build-docker": 285, "run-unit-tests": 268, "e2e-tests": 320}),
    (5002, {"build-docker": 292, "run-unit-tests": 272, "e2e-tests": 315}),
    (5003, {"build-docker": 288, "run-unit-tests": 265, "e2e-tests": 325}),
    (5004, {"build-docker": 294, "run-unit-tests": 275, "e2e-tests": 318}),
]

current_runs_ledger_ci = [
    (6001, {"lint": 113, "integration": 462}),
    (6002, {"lint": 116, "integration": 468}),
    (6003, {"lint": 114, "integration": 460}),
    (6004, {"lint": 117, "integration": 470}),
]

current_runs_auth_audit = [
    (7001, {"security-scan": 153}),
    (7002, {"security-scan": 156}),
    (7003, {"security-scan": 154}),
    (7004, {"security-scan": 155}),
]

sha_counter = [0xabc100]

def next_sha():
    sha_counter[0] += 1
    return f"{sha_counter[0]:040x}"[:40]

# ── Write baseline JSON files ────────────────────────────────────────────────
baseline_dir = WORKSPACE / "artifacts/github-actions/baseline"

for run_id, job_map in baseline_runs_payments_ci:
    jobs = [make_job(name, dur) for name, dur in job_map.items()]
    data = make_run_json(
        run_id, REPO_PAYMENTS, WORKFLOW_CI,
        "main", next_sha(),
        f"https://github.com/{REPO_PAYMENTS}/actions/runs/{run_id}",
        jobs,
    )
    (baseline_dir / f"run-{run_id}.json").write_text(json.dumps(data, indent=2))

for run_id, job_map in baseline_runs_ledger_ci:
    jobs = [make_job(name, dur) for name, dur in job_map.items()]
    data = make_run_json(
        run_id, REPO_LEDGER, WORKFLOW_CI,
        "main", next_sha(),
        f"https://github.com/{REPO_LEDGER}/actions/runs/{run_id}",
        jobs,
    )
    (baseline_dir / f"run-{run_id}.json").write_text(json.dumps(data, indent=2))

for run_id, job_map in baseline_runs_auth_audit:
    jobs = [make_job(name, dur) for name, dur in job_map.items()]
    data = make_run_json(
        run_id, REPO_AUTH, WORKFLOW_AUDIT,
        "main", next_sha(),
        f"https://github.com/{REPO_AUTH}/actions/runs/{run_id}",
        jobs,
    )
    (baseline_dir / f"run-{run_id}.json").write_text(json.dumps(data, indent=2))

# ── Write current JSON files ─────────────────────────────────────────────────
current_dir = WORKSPACE / "artifacts/github-actions/current"

for run_id, job_map in current_runs_payments_ci:
    jobs = [make_job(name, dur) for name, dur in job_map.items()]
    data = make_run_json(
        run_id, REPO_PAYMENTS, WORKFLOW_CI,
        "feature/faster-checkout", next_sha(),
        f"https://github.com/{REPO_PAYMENTS}/actions/runs/{run_id}",
        jobs,
    )
    (current_dir / f"run-{run_id}.json").write_text(json.dumps(data, indent=2))

for run_id, job_map in current_runs_ledger_ci:
    jobs = [make_job(name, dur) for name, dur in job_map.items()]
    data = make_run_json(
        run_id, REPO_LEDGER, WORKFLOW_CI,
        "feature/reconciliation-v2", next_sha(),
        f"https://github.com/{REPO_LEDGER}/actions/runs/{run_id}",
        jobs,
    )
    (current_dir / f"run-{run_id}.json").write_text(json.dumps(data, indent=2))

for run_id, job_map in current_runs_auth_audit:
    jobs = [make_job(name, dur) for name, dur in job_map.items()]
    data = make_run_json(
        run_id, REPO_AUTH, WORKFLOW_AUDIT,
        "main", next_sha(),
        f"https://github.com/{REPO_AUTH}/actions/runs/{run_id}",
        jobs,
    )
    (current_dir / f"run-{run_id}.json").write_text(json.dumps(data, indent=2))

# ── Write the audit script ───────────────────────────────────────────────────
# The skill says "all scripts already exist in the workspace", so we place it.
script_path = WORKSPACE / "skills/github-actions-runtime-regression-audit/scripts/runtime-regression-audit.sh"

AUDIT_SCRIPT = r"""#!/usr/bin/env bash
# GitHub Actions Runtime Regression Audit
# Reads BASELINE_GLOB and CURRENT_GLOB env vars, computes avg+p95 per repo/workflow/job,
# compares and ranks regressions. Honors WARN/CRITICAL thresholds (seconds AND percent).
set -euo pipefail

BASELINE_GLOB="${BASELINE_GLOB:?BASELINE_GLOB is required}"
CURRENT_GLOB="${CURRENT_GLOB:?CURRENT_GLOB is required}"
TOP_N="${TOP_N:-20}"
OUTPUT_FORMAT="${OUTPUT_FORMAT:-text}"
WARN_DELTA_SECONDS="${WARN_DELTA_SECONDS:-30}"
CRITICAL_DELTA_SECONDS="${CRITICAL_DELTA_SECONDS:-90}"
WARN_DELTA_PERCENT="${WARN_DELTA_PERCENT:-15}"
CRITICAL_DELTA_PERCENT="${CRITICAL_DELTA_PERCENT:-35}"
FAIL_ON_CRITICAL="${FAIL_ON_CRITICAL:-0}"
WORKFLOW_MATCH="${WORKFLOW_MATCH:-}"
WORKFLOW_EXCLUDE="${WORKFLOW_EXCLUDE:-}"
JOB_MATCH="${JOB_MATCH:-}"
JOB_EXCLUDE="${JOB_EXCLUDE:-}"
REPO_MATCH="${REPO_MATCH:-}"
REPO_EXCLUDE="${REPO_EXCLUDE:-}"

python3 - <<'PYEOF'
import glob, json, sys, os, re, math

def getenv(k, default=None):
    v = os.environ.get(k, default)
    return v

baseline_glob   = getenv("BASELINE_GLOB")
current_glob    = getenv("CURRENT_GLOB")
top_n           = int(getenv("TOP_N", "20"))
output_format   = getenv("OUTPUT_FORMAT", "text")
warn_sec        = float(getenv("WARN_DELTA_SECONDS", "30"))
crit_sec        = float(getenv("CRITICAL_DELTA_SECONDS", "90"))
warn_pct        = float(getenv("WARN_DELTA_PERCENT", "15"))
crit_pct        = float(getenv("CRITICAL_DELTA_PERCENT", "35"))
fail_on_crit    = getenv("FAIL_ON_CRITICAL", "0") == "1"
wf_match        = getenv("WORKFLOW_MATCH", "")
wf_exclude      = getenv("WORKFLOW_EXCLUDE", "")
job_match       = getenv("JOB_MATCH", "")
job_exclude     = getenv("JOB_EXCLUDE", "")
repo_match      = getenv("REPO_MATCH", "")
repo_exclude    = getenv("REPO_EXCLUDE", "")

def matches(value, include_re, exclude_re):
    if include_re and not re.search(include_re, value):
        return False
    if exclude_re and re.search(exclude_re, value):
        return False
    return True

from datetime import datetime, timezone

def parse_duration(job):
    try:
        fmt = "%Y-%m-%dT%H:%M:%S%z"
        s = datetime.fromisoformat(job["startedAt"])
        e = datetime.fromisoformat(job["completedAt"])
        return max(0.0, (e - s).total_seconds())
    except Exception:
        return None

def p95(values):
    if not values:
        return 0.0
    s = sorted(values)
    idx = math.ceil(0.95 * len(s)) - 1
    idx = max(0, min(idx, len(s)-1))
    return s[idx]

def load_runs(pattern):
    metrics = {}  # key=(repo,workflow,job) -> [duration]
    for fpath in glob.glob(pattern):
        try:
            with open(fpath) as f:
                run = json.load(f)
        except Exception:
            continue
        repo = run.get("repository", {}).get("nameWithOwner", "unknown")
        wf   = run.get("workflowName", "unknown")
        if not matches(repo, repo_match, repo_exclude):
            continue
        if not matches(wf, wf_match, wf_exclude):
            continue
        for job in run.get("jobs", []):
            jname = job.get("name", "unknown")
            if not matches(jname, job_match, job_exclude):
                continue
            dur = parse_duration(job)
            if dur is None:
                continue
            key = (repo, wf, jname)
            metrics.setdefault(key, []).append(dur)
    return metrics

baseline = load_runs(baseline_glob)
current  = load_runs(current_glob)

results = []
new_jobs = []

for key, cur_vals in current.items():
    repo, wf, job = key
    cur_avg = sum(cur_vals) / len(cur_vals)
    cur_p95 = p95(cur_vals)
    if key not in baseline:
        new_jobs.append({"repo": repo, "workflow": wf, "job": job,
                         "current_avg": round(cur_avg, 2),
                         "current_p95": round(cur_p95, 2)})
        continue
    base_vals = baseline[key]
    base_avg = sum(base_vals) / len(base_vals)
    base_p95 = p95(base_vals)
    delta_avg = cur_avg - base_avg
    delta_p95 = cur_p95 - base_p95
    pct_avg   = (delta_avg / base_avg * 100) if base_avg > 0 else 0
    pct_p95   = (delta_p95 / base_p95 * 100) if base_p95 > 0 else 0

    def classify(delta_s, delta_p):
        if delta_s >= crit_sec or delta_p >= crit_pct:
            return "critical"
        if delta_s >= warn_sec or delta_p >= warn_pct:
            return "warn"
        return "ok"

    sev_avg = classify(delta_avg, pct_avg)
    sev_p95 = classify(delta_p95, pct_p95)
    severity = "critical" if "critical" in (sev_avg, sev_p95) else \
               ("warn" if "warn" in (sev_avg, sev_p95) else "ok")

    results.append({
        "repo": repo, "workflow": wf, "job": job,
        "base_avg": round(base_avg, 2), "cur_avg": round(cur_avg, 2),
        "delta_avg": round(delta_avg, 2), "pct_avg": round(pct_avg, 2),
        "base_p95": round(base_p95, 2), "cur_p95": round(cur_p95, 2),
        "delta_p95": round(delta_p95, 2), "pct_p95": round(pct_p95, 2),
        "severity": severity,
    })

results.sort(key=lambda r: r["delta_avg"], reverse=True)
top = results[:top_n]

critical_count = sum(1 for r in results if r["severity"] == "critical")
warn_count     = sum(1 for r in results if r["severity"] == "warn")
ok_count       = sum(1 for r in results if r["severity"] == "ok")

summary = {
    "total_jobs_compared": len(results),
    "critical": critical_count,
    "warn": warn_count,
    "ok": ok_count,
    "new_jobs": len(new_jobs),
}

if output_format == "json":
    out = {"summary": summary, "regressions": top, "new_jobs": new_jobs}
    print(json.dumps(out, indent=2))
else:
    print("=== GitHub Actions Runtime Regression Audit ===")
    print(f"Jobs compared : {summary['total_jobs_compared']}")
    print(f"Critical      : {critical_count}")
    print(f"Warn          : {warn_count}")
    print(f"OK            : {ok_count}")
    print(f"New (no base) : {len(new_jobs)}")
    print()
    print(f"Top {top_n} regressions (sorted by avg delta):")
    print("-" * 80)
    for r in top:
        flag = "🔴 CRITICAL" if r["severity"] == "critical" else \
               ("🟡 WARN" if r["severity"] == "warn" else "🟢 OK")
        print(f"[{flag}] {r['repo']} / {r['workflow']} / {r['job']}")
        print(f"  avg: {r['base_avg']}s → {r['cur_avg']}s  (+{r['delta_avg']}s, +{r['pct_avg']:.1f}%)")
        print(f"  p95: {r['base_p95']}s → {r['cur_p95']}s  (+{r['delta_p95']}s, +{r['pct_p95']:.1f}%)")
    if new_jobs:
        print()
        print("New jobs without baseline:")
        for nj in new_jobs:
            print(f"  {nj['repo']} / {nj['workflow']} / {nj['job']}  avg={nj['current_avg']}s p95={nj['current_p95']}s")

if fail_on_crit and critical_count > 0:
    sys.exit(1)
PYEOF
"""

script_path.write_text(AUDIT_SCRIPT)
script_path.chmod(0o755)

# ── Write a minimal fixture pair (bundled, not used by task) ────────────────
fixtures_dir = WORKSPACE / "skills/github-actions-runtime-regression-audit/fixtures"

fixture_base = {
    "databaseId": 9001,
    "workflowName": "Example CI",
    "headBranch": "main",
    "headSha": "deadbeef" * 5,
    "url": "https://github.com/example/repo/actions/runs/9001",
    "repository": {"nameWithOwner": "example/repo", "name": "repo"},
    "jobs": [{"name": "build", "conclusion": "success",
              "startedAt": "2024-01-01T10:00:00+00:00",
              "completedAt": "2024-01-01T10:01:00+00:00", "steps": []}],
}
fixture_curr = dict(fixture_base, databaseId=9002)
fixture_curr["jobs"] = [{"name": "build", "conclusion": "success",
                          "startedAt": "2024-01-01T10:00:00+00:00",
                          "completedAt": "2024-01-01T10:02:30+00:00", "steps": []}]

(fixtures_dir / "baseline-example.json").write_text(json.dumps(fixture_base, indent=2))
(fixtures_dir / "current-example.json").write_text(json.dumps(fixture_curr, indent=2))

print("Workspace generation complete.")
print(f"Baseline files: {list((WORKSPACE/'artifacts/github-actions/baseline').glob('*.json'))}")
print(f"Current  files: {list((WORKSPACE/'artifacts/github-actions/current').glob('*.json'))}")