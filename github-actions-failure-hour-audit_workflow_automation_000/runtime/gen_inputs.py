#!/usr/bin/env python3
"""
Generate sandbox workspace for the GitHub Actions Failure Hour Audit task.
"""
import os
import json
import random
from pathlib import Path
from datetime import datetime, timedelta, timezone

random.seed(42)

WORKSPACE = os.environ.get("WORKSPACE", "/workspace")

# ── Directory skeleton ─────────────────────────────────────────────────────────
dirs = [
    "artifacts/github-actions",
    "artifacts/coverage",
    "artifacts/lint-reports",
    "artifacts/security-scans",
    "skills/github-actions-failure-hour-audit/scripts",
    "skills/github-actions-failure-hour-audit/docs",
    "skills/github-actions-failure-hour-audit/tests",
    "config/ci",
    "config/alerting",
    "reports/drafts",
    "reports/archive",
    "logs/runners",
    "logs/infra",
    ".github/workflows",
    "scripts/utils",
]
for d in dirs:
    Path(WORKSPACE, d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ───────────────────────────────────────────────────────────
distractor_files = {
    "artifacts/coverage/coverage-summary.json": json.dumps({"total": {"lines": {"pct": 87.4}}}),
    "artifacts/lint-reports/eslint-report.txt": "  3 problems (1 error, 2 warnings)\n",
    "artifacts/security-scans/trivy-results.json": json.dumps({"Results": []}),
    "config/ci/pipeline-config.yaml": "timeout_minutes: 30\nretry_count: 2\n",
    "config/alerting/pagerduty.yaml": "service_key: REDACTED\nthresholds:\n  critical: 5\n",
    "reports/drafts/weekly-summary.md": "# Weekly Summary\nTBD\n",
    "reports/archive/2024-q3-report.json": json.dumps({"quarter": "Q3 2024", "incidents": 12}),
    "logs/runners/runner-001.log": "2024-11-01T08:00:00Z [INFO] Runner started\n",
    "logs/infra/k8s-events.log": "Warning  BackOff  45m   kubelet  Back-off restarting failed container\n",
    ".github/workflows/trading-engine-ci.yml": "name: trading-engine-ci\non: [push]\njobs:\n  build:\n    runs-on: ubuntu-latest\n",
    "scripts/utils/retry.sh": "#!/bin/bash\nfor i in 1 2 3; do $@ && break; done\n",
    "skills/github-actions-failure-hour-audit/docs/architecture.md": "## Architecture\nSee scripts/failure-hour-audit.sh for implementation.\n",
    "skills/github-actions-failure-hour-audit/tests/sample_test.py": "def test_placeholder(): pass\n",
}
for path, content in distractor_files.items():
    fp = Path(WORKSPACE, path)
    fp.write_text(content)


# ── Synthetic GitHub Actions run JSON exports ──────────────────────────────────
# Design goals:
#   - Multiple workflows, multiple branches
#   - Conclusions spanning all failure types AND non-failure types
#   - Timestamps designed so TZ_OFFSET_HOURS=+5 shifts some runs across midnight
#     (UTC 20:xx → local 01:xx next day), creating a new hotspot day/hour
#   - WORKFLOW_MATCH='trading-engine' should keep only that workflow
#   - BRANCH_EXCLUDE='dependabot' should drop those runs
#   - After filtering + tz shift, one hour bucket must cross CRITICAL threshold (>=6)

runs = []

REPO = {"name": "fintech-platform", "nameWithOwner": "acme/fintech-platform"}

def make_run(run_id, workflow, branch, conclusion, created_at_iso):
    return {
        "databaseId": run_id,
        "workflowName": workflow,
        "headBranch": branch,
        "conclusion": conclusion,
        "createdAt": created_at_iso,
        "updatedAt": created_at_iso,
        "url": f"https://github.com/acme/fintech-platform/actions/runs/{run_id}",
        "repository": REPO,
    }

base_date = datetime(2024, 11, 12, tzinfo=timezone.utc)  # Tuesday

# ── Bucket A: trading-engine-ci, main branch, UTC 20:00–21:00 (→ local 01:00–02:00 Wed)
# These should form a CRITICAL cluster in the TZ-shifted view (Wed 01:xx)
for i in range(7):
    dt = base_date.replace(hour=20, minute=i*5)
    conclusion = random.choice(["failure", "timed_out", "failure", "cancelled", "failure"])
    runs.append(make_run(10000+i, "trading-engine-ci", "main", conclusion,
                         dt.strftime("%Y-%m-%dT%H:%M:%SZ")))

# ── Bucket B: trading-engine-ci, main branch, UTC 08:00–09:00 Tue (→ local 13:00–14:00)
# WARN-level cluster (4 failures)
for i in range(4):
    dt = base_date.replace(hour=8, minute=i*10)
    runs.append(make_run(10100+i, "trading-engine-ci", "main", "failure",
                         dt.strftime("%Y-%m-%dT%H:%M:%SZ")))

# ── Bucket C: trading-engine-ci, dependabot branches — MUST BE EXCLUDED by BRANCH_EXCLUDE
for i in range(8):
    dt = base_date.replace(hour=20, minute=i*6)
    runs.append(make_run(10200+i, "trading-engine-ci", "dependabot/npm/lodash-4.17.21",
                         "failure", dt.strftime("%Y-%m-%dT%H:%M:%SZ")))

# ── Bucket D: infra-deploy workflow — MUST BE EXCLUDED by WORKFLOW_MATCH='trading-engine'
for i in range(5):
    dt = base_date.replace(hour=20, minute=i*8)
    runs.append(make_run(10300+i, "infra-deploy", "main", "failure",
                         dt.strftime("%Y-%m-%dT%H:%M:%SZ")))

# ── Bucket E: trading-engine-ci successes — must be filtered out (non-failure conclusion)
for i in range(10):
    dt = base_date.replace(hour=14, minute=i*5)
    runs.append(make_run(10400+i, "trading-engine-ci", "main", "success",
                         dt.strftime("%Y-%m-%dT%H:%M:%SZ")))

# ── Bucket F: trading-engine-ci, release branch, startup_failure at UTC 03:00 (→ local 08:00)
for i in range(3):
    dt = base_date.replace(hour=3, minute=i*15)
    runs.append(make_run(10500+i, "trading-engine-ci", "release/2024-q4", "startup_failure",
                         dt.strftime("%Y-%m-%dT%H:%M:%SZ")))

# ── Bucket G: trading-engine-ci, main, action_required at UTC 15:00 (→ local 20:00)
for i in range(2):
    dt = base_date.replace(hour=15, minute=i*20)
    runs.append(make_run(10600+i, "trading-engine-ci", "main", "action_required",
                         dt.strftime("%Y-%m-%dT%H:%M:%SZ")))

# ── Bucket H: trading-engine-ci, main, neutral/skipped (non-failures to be filtered)
for i in range(5):
    dt = base_date.replace(hour=10, minute=i*7)
    c = random.choice(["skipped", "neutral", "success"])
    runs.append(make_run(10700+i, "trading-engine-ci", "main", c,
                         dt.strftime("%Y-%m-%dT%H:%M:%SZ")))

# Write one JSON file per run
random.shuffle(runs)
for run in runs:
    fname = f"run-{run['databaseId']}.json"
    fp = Path(WORKSPACE, "artifacts/github-actions", fname)
    fp.write_text(json.dumps(run, indent=2))

# ── Stub for failure-hour-audit.sh ────────────────────────────────────────────
# The script already exists per SKILL.md; we create a realistic implementation
# that honours all documented env-var contracts.
script_path = Path(WORKSPACE, "skills/github-actions-failure-hour-audit/scripts/failure-hour-audit.sh")

SCRIPT_CONTENT = r'''#!/usr/bin/env bash
# failure-hour-audit.sh  – GitHub Actions Failure Hour Audit skill
set -euo pipefail

RUN_GLOB="${RUN_GLOB:-artifacts/github-actions/*.json}"
TOP_N="${TOP_N:-24}"
OUTPUT_FORMAT="${OUTPUT_FORMAT:-text}"
WARN_FAILURE_RUNS="${WARN_FAILURE_RUNS:-3}"
CRITICAL_FAILURE_RUNS="${CRITICAL_FAILURE_RUNS:-6}"
FAIL_ON_CRITICAL="${FAIL_ON_CRITICAL:-0}"
TZ_OFFSET_HOURS="${TZ_OFFSET_HOURS:-0}"
WORKFLOW_MATCH="${WORKFLOW_MATCH:-}"
WORKFLOW_EXCLUDE="${WORKFLOW_EXCLUDE:-}"
BRANCH_MATCH="${BRANCH_MATCH:-}"
BRANCH_EXCLUDE="${BRANCH_EXCLUDE:-}"
REPO_MATCH="${REPO_MATCH:-}"
REPO_EXCLUDE="${REPO_EXCLUDE:-}"

FAILURE_CONCLUSIONS="failure|cancelled|timed_out|action_required|startup_failure"

python3 - <<'PYEOF'
import sys, os, json, glob, re
from datetime import datetime, timezone, timedelta

run_glob              = os.environ.get("RUN_GLOB", "artifacts/github-actions/*.json")
top_n                 = int(os.environ.get("TOP_N", "24"))
output_format         = os.environ.get("OUTPUT_FORMAT", "text").lower()
warn_threshold        = int(os.environ.get("WARN_FAILURE_RUNS", "3"))
critical_threshold    = int(os.environ.get("CRITICAL_FAILURE_RUNS", "6"))
fail_on_critical      = os.environ.get("FAIL_ON_CRITICAL", "0") == "1"
tz_offset_hours       = int(os.environ.get("TZ_OFFSET_HOURS", "0"))
workflow_match        = os.environ.get("WORKFLOW_MATCH", "")
workflow_exclude      = os.environ.get("WORKFLOW_EXCLUDE", "")
branch_match          = os.environ.get("BRANCH_MATCH", "")
branch_exclude        = os.environ.get("BRANCH_EXCLUDE", "")
repo_match            = os.environ.get("REPO_MATCH", "")
repo_exclude          = os.environ.get("REPO_EXCLUDE", "")

FAILURE_CONCLUSIONS = {"failure", "cancelled", "timed_out", "action_required", "startup_failure"}

tz = timezone(timedelta(hours=tz_offset_hours))

files = glob.glob(run_glob)
records = []
for f in files:
    try:
        data = json.loads(open(f).read())
        # handle both single-run and list formats
        if isinstance(data, list):
            records.extend(data)
        else:
            records.append(data)
    except Exception:
        continue

def repo_name(r):
    repo = r.get("repository", {})
    if isinstance(repo, dict):
        return repo.get("nameWithOwner") or repo.get("name") or ""
    return str(repo)

# filter
filtered = []
for r in records:
    conclusion = (r.get("conclusion") or "").lower()
    if conclusion not in FAILURE_CONCLUSIONS:
        continue
    wf = r.get("workflowName", "")
    br = r.get("headBranch", "")
    rp = repo_name(r)
    if workflow_match and not re.search(workflow_match, wf):
        continue
    if workflow_exclude and re.search(workflow_exclude, wf):
        continue
    if branch_match and not re.search(branch_match, br):
        continue
    if branch_exclude and re.search(branch_exclude, br):
        continue
    if repo_match and not re.search(repo_match, rp):
        continue
    if repo_exclude and re.search(repo_exclude, rp):
        continue
    filtered.append(r)

# bucket by local day-of-week + hour
buckets = {}
for r in filtered:
    raw_ts = r.get("createdAt", "")
    try:
        dt_utc = datetime.strptime(raw_ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        dt_local = dt_utc.astimezone(tz)
    except Exception:
        continue
    key = (dt_local.strftime("%A"), dt_local.hour)
    buckets[key] = buckets.get(key, 0) + 1

# rank
ranked = sorted(buckets.items(), key=lambda x: x[1], reverse=True)[:top_n]

def severity(count):
    if count >= critical_threshold:
        return "critical"
    if count >= warn_threshold:
        return "warn"
    return "ok"

total_failures = sum(buckets.values())
total_windows  = len(buckets)
critical_windows = [(k, v) for k, v in ranked if severity(v) == "critical"]

if output_format == "json":
    windows_out = []
    for (day, hour), count in ranked:
        windows_out.append({
            "day": day,
            "hour": hour,
            "failure_runs": count,
            "severity": severity(count),
        })
    result = {
        "summary": {
            "total_failure_runs": total_failures,
            "total_windows": total_windows,
            "warn_threshold": warn_threshold,
            "critical_threshold": critical_threshold,
            "tz_offset_hours": tz_offset_hours,
        },
        "windows": windows_out,
        "critical_windows": [{"day": k[0], "hour": k[1], "failure_runs": v} for k, v in critical_windows],
    }
    print(json.dumps(result, indent=2))
else:
    print(f"=== GitHub Actions Failure Hour Audit ===")
    print(f"Total failure runs : {total_failures}")
    print(f"Total windows      : {total_windows}")
    print(f"TZ offset          : {tz_offset_hours:+d}h")
    print(f"Thresholds         : warn>={warn_threshold}  critical>={critical_threshold}")
    print()
    print(f"Top {top_n} windows:")
    for (day, hour), count in ranked:
        sev = severity(count).upper()
        print(f"  [{sev:8s}] {day:9s} {hour:02d}:00  failures={count}")

if fail_on_critical and critical_windows:
    sys.exit(1)
sys.exit(0)
PYEOF
'''

script_path.write_text(SCRIPT_CONTENT)
script_path.chmod(0o755)

print("Workspace generated successfully.")
print(f"  Run JSONs:  {len(runs)} files in artifacts/github-actions/")
print(f"  Distractors: {len(distractor_files)} files")