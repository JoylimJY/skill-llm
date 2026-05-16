#!/usr/bin/env bash
set -euo pipefail

# Fix Python script heredoc quoting issue from gen_inputs
SKILL_DIR="/workspace/skills/github-actions-duplicate-run-audit/scripts"
PY_FILE="$SKILL_DIR/duplicate-run-audit.py"

# Rewrite the Python file cleanly (the gen_inputs string replacement may be fragile)
cat > "$PY_FILE" << 'PYEOF'
#!/usr/bin/env python3
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
            items = data if isinstance(data, list) else [data]
            for run in items:
                repo = ''
                if isinstance(run.get('repository'), dict):
                    repo = run['repository'].get('nameWithOwner') or run['repository'].get('full_name') or ''
                elif isinstance(run.get('repository'), str):
                    repo = run['repository']
                run['_repo'] = repo
                wf     = run.get('workflowName') or run.get('name') or ''
                branch = run.get('headBranch') or ''
                event  = run.get('event') or ''
                sha    = run.get('headSha') or ''
                if not regex_match(wf,     args.workflow_match):   continue
                if args.workflow_exclude and regex_match(wf,     args.workflow_exclude): continue
                if not regex_match(branch, args.branch_match):     continue
                if args.branch_exclude  and regex_match(branch, args.branch_exclude):   continue
                if not regex_match(event,  args.event_match):      continue
                if args.event_exclude   and regex_match(event,  args.event_exclude):    continue
                if not regex_match(repo,   args.repo_match):       continue
                if args.repo_exclude    and regex_match(repo,   args.repo_exclude):     continue
                if not regex_match(sha,    args.head_sha_match):   continue
                if args.head_sha_exclude and regex_match(sha,   args.head_sha_exclude): continue
                runs.append(run)
        except Exception:
            pass
    return runs

def cluster_bursts(runs, window_minutes):
    groups = defaultdict(list)
    for run in runs:
        key = (
            run.get('_repo', ''),
            run.get('workflowName') or run.get('name') or '',
            run.get('headBranch', ''),
            run.get('event', ''),
            run.get('headSha', ''),
        )
        groups[key].append(run)

    bursts = []
    for key, grp in groups.items():
        grp.sort(key=lambda r: parse_dt(r.get('createdAt')) or datetime.min.replace(tzinfo=timezone.utc))
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
    result.sort(key=lambda x: x['wasted_minutes'], reverse=True)
    return result

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--run-glob',                default='artifacts/github-actions/*.json')
    p.add_argument('--top-n',                   type=int,   default=20)
    p.add_argument('--output-format',           default='text')
    p.add_argument('--duplicate-window-minutes',type=float, default=30)
    p.add_argument('--min-duplicate-runs',      type=int,   default=2)
    p.add_argument('--warn-duplicate-runs',     type=int,   default=3)
    p.add_argument('--critical-duplicate-runs', type=int,   default=6)
    p.add_argument('--warn-wasted-minutes',     type=float, default=20)
    p.add_argument('--critical-wasted-minutes', type=float, default=60)
    p.add_argument('--workflow-match',          default='')
    p.add_argument('--workflow-exclude',        default='')
    p.add_argument('--branch-match',            default='')
    p.add_argument('--branch-exclude',          default='')
    p.add_argument('--event-match',             default='')
    p.add_argument('--event-exclude',           default='')
    p.add_argument('--repo-match',              default='')
    p.add_argument('--repo-exclude',            default='')
    p.add_argument('--head-sha-match',          default='')
    p.add_argument('--head-sha-exclude',        default='')
    p.add_argument('--fail-on-critical',        type=int,   default=0)
    args = p.parse_args()

    runs   = load_runs(args.run_glob, args)
    bursts = cluster_bursts(runs, args.duplicate_window_minutes)
    groups = build_groups(bursts, args)
    top    = groups[:args.top_n]
    critical_groups = [g for g in groups if g['severity'] == 'critical']
    total_wasted    = sum(g['wasted_minutes'] for g in groups)
    summary = {
        'total_runs_analyzed': len(runs),
        'duplicate_groups':    len(groups),
        'critical_groups':     len(critical_groups),
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
        print(f"Runs analyzed   : {summary['total_runs_analyzed']}")
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
PYEOF

chmod +x "$PY_FILE"
chmod +x "$SKILL_DIR/duplicate-run-audit.sh"

echo "Setup complete. Skill scripts are executable."
ls -la "$SKILL_DIR/"