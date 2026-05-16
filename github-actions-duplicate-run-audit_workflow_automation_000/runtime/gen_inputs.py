#!/usr/bin/env python3
"""
Generate a realistic, messy sandbox workspace for the GitHub Actions Duplicate Run Audit task.
Deterministic: uses fixed random seed.
"""

import json
import os
import random
import string
from datetime import datetime, timezone, timedelta
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ---------------------------------------------------------------------------
# 1. Skill directory structure (already exists per SKILL.md contract)
# ---------------------------------------------------------------------------
skill_dir = WORKSPACE / "skills" / "github-actions-duplicate-run-audit"
scripts_dir = skill_dir / "scripts"
fixtures_dir = skill_dir / "fixtures"

for d in [scripts_dir, fixtures_dir]:
    d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# 2. Create the duplicate-run-audit.sh script (the skill script itself)
# ---------------------------------------------------------------------------
audit_sh = scripts_dir / "duplicate-run-audit.sh"
audit_sh.write_text(r"""#!/usr/bin/env bash
set -euo pipefail

RUN_GLOB="${RUN_GLOB:-artifacts/github-actions/*.json}"
TOP_N="${TOP_N:-20}"
OUTPUT_FORMAT="${OUTPUT_FORMAT:-text}"
DUPLICATE_WINDOW_MINUTES="${DUPLICATE_WINDOW_MINUTES:-30}"
MIN_DUPLICATE_RUNS="${MIN_DUPLICATE_RUNS:-2}"
WARN_DUPLICATE_RUNS="${WARN_DUPLICATE_RUNS:-3}"
CRITICAL_DUPLICATE_RUNS="${CRITICAL_DUPLICATE_RUNS:-6}"
WARN_WASTED_MINUTES="${WARN_WASTED_MINUTES:-20}"
CRITICAL_WASTED_MINUTES="${CRITICAL_WASTED_MINUTES:-60}"
WORKFLOW_MATCH="${WORKFLOW_MATCH:-}"
WORKFLOW_EXCLUDE="${WORKFLOW_EXCLUDE:-}"
BRANCH_MATCH="${BRANCH_MATCH:-}"
BRANCH_EXCLUDE="${BRANCH_EXCLUDE:-}"
EVENT_MATCH="${EVENT_MATCH:-}"
EVENT_EXCLUDE="${EVENT_EXCLUDE:-}"
REPO_MATCH="${REPO_MATCH:-}"
REPO_EXCLUDE="${REPO_EXCLUDE:-}"
HEAD_SHA_MATCH="${HEAD_SHA_MATCH:-}"
HEAD_SHA_EXCLUDE="${HEAD_SHA_EXCLUDE:-}"
FAIL_ON_CRITICAL="${FAIL_ON_CRITICAL:-0}"

python3 "$(dirname "$0")/duplicate-run-audit.py" \
    --run-glob     "$RUN_GLOB" \
    --top-n        "$TOP_N" \
    --output-format "$OUTPUT_FORMAT" \
    --duplicate-window-minutes "$DUPLICATE_WINDOW_MINUTES" \
    --min-duplicate-runs "$MIN_DUPLICATE_RUNS" \
    --warn-duplicate-runs "$WARN_DUPLICATE_RUNS" \
    --critical-duplicate-runs "$CRITICAL_DUPLICATE_RUNS" \
    --warn-wasted-minutes "$WARN_WASTED_MINUTES" \
    --critical-wasted-minutes "$CRITICAL_WASTED_MINUTES" \
    ${WORKFLOW_MATCH:+--workflow-match "$WORKFLOW_MATCH"} \
    ${WORKFLOW_EXCLUDE:+--workflow-exclude "$WORKFLOW_EXCLUDE"} \
    ${BRANCH_MATCH:+--branch-match "$BRANCH_MATCH"} \
    ${BRANCH_EXCLUDE:+--branch-exclude "$BRANCH_EXCLUDE"} \
    ${EVENT_MATCH:+--event-match "$EVENT_MATCH"} \
    ${EVENT_EXCLUDE:+--event-exclude "$EVENT_EXCLUDE"} \
    ${REPO_MATCH:+--repo-match "$REPO_MATCH"} \
    ${REPO_EXCLUDE:+--repo-exclude "$REPO_EXCLUDE"} \
    ${HEAD_SHA_MATCH:+--head-sha-match "$HEAD_SHA_MATCH"} \
    ${HEAD_SHA_EXCLUDE:+--head-sha-exclude "$HEAD_SHA_EXCLUDE"} \
    ${FAIL_ON_CRITICAL:+--fail-on-critical "$FAIL_ON_CRITICAL"}
""")
audit_sh.chmod(0o755)

# ---------------------------------------------------------------------------
# 3. Create the Python implementation
# ---------------------------------------------------------------------------
audit_py = scripts_dir / "duplicate-run-audit.py"
audit_py.write_text(r'''#!/usr/bin/env python3
"""GitHub Actions Duplicate Run Audit - core implementation"""
import argparse
import glob
import json
import re
import sys
from datetime import datetime, timezone
from collections import defaultdict

def parse_dt(s):
    if not s:
        return None
    s = s.rstrip('Z')
    for fmt in ('%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f'):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return None

def duration_minutes(run):
    started = parse_dt(run.get('startedAt') or run.get('createdAt'))
    updated = parse_dt(run.get('updatedAt'))
    if started and updated and updated > started:
        return (updated - started).total_seconds() / 60.0
    return 0.0

def regex_match(value, pattern):
    if not pattern:
        return True
    return bool(re.search(pattern, value or ''))

def load_runs(run_glob, args):
    runs = []
    for path in glob.glob(run_glob, recursive=True):
        try:
            with open(path) as f:
                data = json.load(f)
            # support single run or list
            if isinstance(data, list):
                items = data
            else:
                items = [data]
            for run in items:
                # Extract repo name
                repo = ''
                if isinstance(run.get('repository'), dict):
                    repo = run['repository'].get('nameWithOwner') or run['repository'].get('full_name') or ''
                elif isinstance(run.get('repository'), str):
                    repo = run['repository']
                run['_repo'] = repo
                # Filters
                wf = run.get('workflowName') or run.get('name') or ''
                branch = run.get('headBranch') or ''
                event = run.get('event') or ''
                sha = run.get('headSha') or ''
                if not regex_match(wf, args.workflow_match): continue
                if args.workflow_exclude and regex_match(wf, args.workflow_exclude): continue
                if not regex_match(branch, args.branch_match): continue
                if args.branch_exclude and regex_match(branch, args.branch_exclude): continue
                if not regex_match(event, args.event_match): continue
                if args.event_exclude and regex_match(event, args.event_exclude): continue
                if not regex_match(repo, args.repo_match): continue
                if args.repo_exclude and regex_match(repo, args.repo_exclude): continue
                if not regex_match(sha, args.head_sha_match): continue
                if args.head_sha_exclude and regex_match(sha, args.head_sha_exclude): continue
                runs.append(run)
        except Exception:
            pass
    return runs

def cluster_bursts(runs, window_minutes):
    # Group by (repo, workflow, branch, event, sha)
    groups = defaultdict(list)
    for run in runs:
        key = (
            run.get('_repo',''),
            run.get('workflowName') or run.get('name') or '',
            run.get('headBranch',''),
            run.get('event',''),
            run.get('headSha',''),
        )
        groups[key].append(run)

    bursts = []
    for key, grp in groups.items():
        # Sort by createdAt
        grp.sort(key=lambda r: parse_dt(r.get('createdAt')) or datetime.min.replace(tzinfo=timezone.utc))
        # Cluster by time window
        if not grp:
            continue
        clusters = []
        current = [grp[0]]
        for run in grp[1:]:
            t0 = parse_dt(current[0].get('createdAt'))
            t1 = parse_dt(run.get('createdAt'))
            if t0 and t1 and (t1 - t0).total_seconds() <= window_minutes * 60:
                current.append(run)
            else:
                clusters.append(current)
                current = [run]
        clusters.append(current)
        for cluster in clusters:
            bursts.append((key, cluster))
    return bursts

def score_severity(run_count, wasted_min, args):
    if run_count >= args.critical_duplicate_runs or wasted_min >= args.critical_wasted_minutes:
        return 'critical'
    if run_count >= args.warn_duplicate_runs or wasted_min >= args.warn_wasted_minutes:
        return 'warn'
    return 'ok'

def build_groups(bursts, args):
    result = []
    for (repo, wf, branch, event, sha), cluster in bursts:
        run_count = len(cluster)
        if run_count < args.min_duplicate_runs:
            continue
        durations = [duration_minutes(r) for r in cluster]
        total_min = sum(durations)
        # wasted = total minus the first (canonical) run
        wasted_min = sum(durations[1:]) if len(durations) > 1 else 0.0
        severity = score_severity(run_count, wasted_min, args)
        result.append({
            'repo': repo,
            'workflow': wf,
            'branch': branch,
            'event': event,
            'head_sha': sha,
            'run_count': run_count,
            'total_minutes': round(total_min, 2),
            'wasted_minutes': round(wasted_min, 2),
            'severity': severity,
            'run_ids': [r.get('databaseId') for r in cluster],
            'created_at_first': (cluster[0].get('createdAt') or ''),
        })
    # rank by wasted_minutes desc
    result.sort(key=lambda x: x['wasted_minutes'], reverse=True)
    return result

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--run-glob', default='artifacts/github-actions/*.json')
    p.add_argument('--top-n', type=int, default=20)
    p.add_argument('--output-format', default='text')
    p.add_argument('--duplicate-window-minutes', type=float, default=30)
    p.add_argument('--min-duplicate-runs', type=int, default=2)
    p.add_argument('--warn-duplicate-runs', type=int, default=3)
    p.add_argument('--critical-duplicate-runs', type=int, default=6)
    p.add_argument('--warn-wasted-minutes', type=float, default=20)
    p.add_argument('--critical-wasted-minutes', type=float, default=60)
    p.add_argument('--workflow-match', default='')
    p.add_argument('--workflow-exclude', default='')
    p.add_argument('--branch-match', default='')
    p.add_argument('--branch-exclude', default='')
    p.add_argument('--event-match', default='')
    p.add_argument('--event-exclude', default='')
    p.add_argument('--repo-match', default='')
    p.add_argument('--repo-exclude', default='')
    p.add_argument('--head-sha-match', default='')
    p.add_argument('--head-sha-exclude', default='')
    p.add_argument('--fail-on-critical', type=int, default=0)
    args = p.parse_args()

    runs = load_runs(args.run_glob, args)
    bursts = cluster_bursts(runs, args.duplicate_window_minutes)
    groups = build_groups(bursts, args)
    top = groups[:args.top_n]
    critical_groups = [g for g in groups if g['severity'] == 'critical']
    total_wasted = sum(g['wasted_minutes'] for g in groups)
    summary = {
        'total_runs_analyzed': len(runs),
        'duplicate_groups': len(groups),
        'critical_groups': len(critical_groups),
        'total_wasted_minutes': round(total_wasted, 2),
    }

    if args.output_format == 'json':
        out = {
            'summary': summary,
            'top_groups': top,
            'critical_groups': critical_groups,
        }
        print(json.dumps(out, indent=2))
    else:
        print("=== GitHub Actions Duplicate Run Audit ===")
        print(f"Runs analyzed  : {summary['total_runs_analyzed']}")
        print(f"Duplicate groups: {summary['duplicate_groups']}")
        print(f"Critical groups : {summary['critical_groups']}")
        print(f"Total wasted min: {summary['total_wasted_minutes']}")
        print()
        for i, g in enumerate(top, 1):
            print(f"[{i}] [{g['severity'].upper()}] {g['repo']} / {g['workflow']} / {g['branch']} ({g['event']})")
            print(f"    SHA: {g['head_sha'][:12]}  runs={g['run_count']}  wasted={g['wasted_minutes']}min")

    if args.fail_on_critical and critical_groups:
        sys.exit(1)
    sys.exit(0)

if __name__ == '__main__':
    main()
''')
audit_py.chmod(0o755)

# ---------------------------------------------------------------------------
# 4. Generate synthetic run JSON files in artifacts/github-actions/
# ---------------------------------------------------------------------------
artifacts_dir = WORKSPACE / "artifacts" / "github-actions"
artifacts_dir.mkdir(parents=True, exist_ok=True)

def make_run(run_id, workflow, branch, event, sha, repo, created_offset_seconds,
             duration_seconds=120, conclusion="success"):
    base = datetime(2024, 3, 15, 10, 0, 0, tzinfo=timezone.utc)
    created = base + timedelta(seconds=created_offset_seconds)
    started = created + timedelta(seconds=5)
    updated = started + timedelta(seconds=duration_seconds)
    return {
        "databaseId": run_id,
        "workflowName": workflow,
        "event": event,
        "conclusion": conclusion,
        "headBranch": branch,
        "headSha": sha,
        "createdAt": created.strftime('%Y-%m-%dT%H:%M:%SZ'),
        "startedAt": started.strftime('%Y-%m-%dT%H:%M:%SZ'),
        "updatedAt": updated.strftime('%Y-%m-%dT%H:%M:%SZ'),
        "url": f"https://github.com/{repo}/actions/runs/{run_id}",
        "repository": {"nameWithOwner": repo},
    }

# SHA constants
SHA_PAYMENT = "abc123def456abc123def456abc123def456abc1"
SHA_DEPLOY  = "111aaa222bbb333ccc444ddd555eee666fff7777"
SHA_HOTFIX  = "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef"
SHA_CANARY  = "cafebabecafebabecafebabecafebabecafebabe"
SHA_INFRA   = "9999999999999999999999999999999999999999"
SHA_LINT    = "aaaabbbbccccddddeeeeffffaaaabbbbccccdddd"

run_id = 10000

# Group A: payment-ci on main, push, SHA_PAYMENT — 8 runs in 25 min window
# These SHOULD be critical with custom thresholds (critical_duplicate_runs=5)
group_a_offsets = [0, 120, 300, 600, 900, 1200, 1350, 1490]  # all within 25 min
for i, offset in enumerate(group_a_offsets):
    run = make_run(run_id, "payment-ci", "main", "push", SHA_PAYMENT,
                   "fintech-corp/payment-service", offset, duration_seconds=480)
    (artifacts_dir / f"run-{run_id}.json").write_text(json.dumps(run, indent=2))
    run_id += 1

# Group B: deploy-staging on release/v2, workflow_dispatch, SHA_DEPLOY — 4 runs in 15 min
group_b_offsets = [0, 200, 500, 800]
for i, offset in enumerate(group_b_offsets):
    run = make_run(run_id, "deploy-staging", "release/v2", "workflow_dispatch", SHA_DEPLOY,
                   "fintech-corp/payment-service", 10000 + offset, duration_seconds=600)
    (artifacts_dir / f"run-{run_id}.json").write_text(json.dumps(run, indent=2))
    run_id += 1

# Group C: payment-ci on hotfix/pci-patch, push, SHA_HOTFIX — 3 runs
# SHOULD BE EXCLUDED by branch_exclude=hotfix
group_c_offsets = [0, 150, 400]
for i, offset in enumerate(group_c_offsets):
    run = make_run(run_id, "payment-ci", "hotfix/pci-patch", "push", SHA_HOTFIX,
                   "fintech-corp/payment-service", 20000 + offset, duration_seconds=300)
    (artifacts_dir / f"run-{run_id}.json").write_text(json.dumps(run, indent=2))
    run_id += 1

# Group D: canary-test on main, schedule, SHA_CANARY — 5 runs
# SHOULD BE EXCLUDED by event_exclude=schedule
group_d_offsets = [0, 100, 250, 400, 600]
for i, offset in enumerate(group_d_offsets):
    run = make_run(run_id, "canary-test", "main", "schedule", SHA_CANARY,
                   "fintech-corp/payment-service", 30000 + offset, duration_seconds=200)
    (artifacts_dir / f"run-{run_id}.json").write_text(json.dumps(run, indent=2))
    run_id += 1

# Group E: infra-validate on main, push, SHA_INFRA — 2 runs (borderline, should appear)
group_e_offsets = [0, 300]
for i, offset in enumerate(group_e_offsets):
    run = make_run(run_id, "infra-validate", "main", "push", SHA_INFRA,
                   "fintech-corp/infra-repo", 40000 + offset, duration_seconds=180)
    (artifacts_dir / f"run-{run_id}.json").write_text(json.dumps(run, indent=2))
    run_id += 1

# Group F: lint-check on feature/add-kyc, push, SHA_LINT — 2 runs
# SHOULD BE EXCLUDED because workflow_match=payment-ci|deploy-staging|infra-validate
group_f_offsets = [0, 200]
for i, offset in enumerate(group_f_offsets):
    run = make_run(run_id, "lint-check", "feature/add-kyc", "push", SHA_LINT,
                   "fintech-corp/payment-service", 50000 + offset, duration_seconds=60)
    (artifacts_dir / f"run-{run_id}.json").write_text(json.dumps(run, indent=2))
    run_id += 1

# Group G: deploy-staging on main push — 7 runs in 30 min window (should be critical)
SHA_G = "bbbb1111bbbb2222bbbb3333bbbb4444bbbb5555"
group_g_offsets = [0, 150, 400, 650, 900, 1100, 1700]
for i, offset in enumerate(group_g_offsets):
    run = make_run(run_id, "deploy-staging", "main", "push", SHA_G,
                   "fintech-corp/payment-service", 60000 + offset, duration_seconds=700)
    (artifacts_dir / f"run-{run_id}.json").write_text(json.dumps(run, indent=2))
    run_id += 1

# Singleton runs (no duplicates — noise)
singletons = [
    ("payment-ci", "develop", "push", "solo111", "fintech-corp/payment-service", 70000, 90),
    ("deploy-prod", "main", "workflow_dispatch", "solo222", "fintech-corp/payment-service", 71000, 800),
    ("security-scan", "main", "push", "solo333", "fintech-corp/infra-repo", 72000, 400),
]
for wf, br, ev, sha, repo, base_off, dur in singletons:
    run = make_run(run_id, wf, br, ev, sha, repo, base_off, dur)
    (artifacts_dir / f"run-{run_id}.json").write_text(json.dumps(run, indent=2))
    run_id += 1

# ---------------------------------------------------------------------------
# 5. Distractor directory structure
# ---------------------------------------------------------------------------
distractor_dirs = [
    WORKSPACE / "reports" / "ci-metrics",
    WORKSPACE / "reports" / "security",
    WORKSPACE / "config" / "ci",
    WORKSPACE / "config" / "monitoring",
    WORKSPACE / "docs" / "runbooks",
    WORKSPACE / "scripts" / "helpers",
    WORKSPACE / "data" / "archived" / "2023",
    WORKSPACE / "data" / "archived" / "2022",
    WORKSPACE / ".github" / "workflows",
    WORKSPACE / "terraform" / "modules" / "ci",
]
for d in distractor_dirs:
    d.mkdir(parents=True, exist_ok=True)

distractors = [
    (WORKSPACE / "reports" / "ci-metrics" / "weekly_summary.csv",
     "week,total_runs,pass_rate\n2024-W10,342,0.94\n2024-W11,289,0.91\n"),
    (WORKSPACE / "reports" / "ci-metrics" / "flaky_tests.txt",
     "test_payment_gateway_timeout - flaky 8/20\ntest_kyc_idempotency - flaky 3/20\n"),
    (WORKSPACE / "reports" / "security" / "sast_findings.json",
     json.dumps({"critical": 0, "high": 2, "medium": 14})),
    (WORKSPACE / "config" / "ci" / "thresholds.yaml",
     "flaky_rate_warn: 0.15\nflaky_rate_critical: 0.30\nbuild_time_warn_minutes: 15\n"),
    (WORKSPACE / "config" / "monitoring" / "alerting.yaml",
     "channels:\n  - slack: '#platform-alerts'\n  - pagerduty: P123XYZ\n"),
    (WORKSPACE / "docs" / "runbooks" / "ci-triage.md",
     "# CI Triage Runbook\n\nIf builds are failing, check the deploy-staging logs first.\n"),
    (WORKSPACE / "scripts" / "helpers" / "fetch_runs.sh",
     "#!/usr/bin/env bash\n# Not a real script — placeholder\necho 'fetch runs'\n"),
    (WORKSPACE / "data" / "archived" / "2023" / "ci_events.log",
     "2023-11-01T08:00:00Z run 5001 started\n2023-11-01T08:12:00Z run 5001 completed\n"),
    (WORKSPACE / "data" / "archived" / "2022" / "run_index.txt",
     "run_id,status\n1001,success\n1002,failure\n1003,success\n"),
    (WORKSPACE / ".github" / "workflows" / "payment-ci.yml",
     "name: payment-ci\non: [push]\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps: []\n"),
    (WORKSPACE / ".github" / "workflows" / "deploy-staging.yml",
     "name: deploy-staging\non: [workflow_dispatch, push]\njobs:\n  deploy:\n    runs-on: ubuntu-latest\n    steps: []\n"),
    (WORKSPACE / "terraform" / "modules" / "ci" / "main.tf",
     'resource "aws_iam_role" "ci_role" {\n  name = "ci-runner"\n}\n'),
]
for path, content in distractors:
    path.write_text(content)

# ---------------------------------------------------------------------------
# 6. Write the task context file (not hints, just business context)
# ---------------------------------------------------------------------------
context_file = WORKSPACE / "TASK_CONTEXT.md"
context_file.write_text("""# Q1 CI Hygiene Audit — FinTech Platform Engineering

Our platform team needs a machine-readable waste report for the payment-processing CI pipeline.

## Scope
- Repository data is in: artifacts/github-actions/
- The audit tooling lives under: skills/github-actions-duplicate-run-audit/

## Deliverable
Save the audit results to: ci_waste_report.json
""")

print("Workspace generated successfully.")
print(f"Run JSON files created: {len(list(artifacts_dir.glob('*.json')))}")