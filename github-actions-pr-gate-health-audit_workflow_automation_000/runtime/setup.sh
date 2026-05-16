#!/usr/bin/env bash
set -euo pipefail

WORKSPACE=/workspace

# ── Install the skill scripts from the public repo ────────────────────────────
# The skill's script directory must exist and be executable.
SKILL_DIR="$WORKSPACE/skills/github-actions-pr-gate-health-audit/scripts"
mkdir -p "$SKILL_DIR"

# Download the actual skill script from the public openclaw registry / GitHub
# Using the documented path structure from SKILL.md
SCRIPT_PATH="$SKILL_DIR/pr-gate-health-audit.sh"

# Write the canonical pr-gate-health-audit.sh implementation
# This implements exactly what SKILL.md specifies.
cat > "$SCRIPT_PATH" << 'BASH_EOF'
#!/usr/bin/env bash
# pr-gate-health-audit.sh — GitHub Actions PR Gate Health Audit
set -euo pipefail

RUN_GLOB="${RUN_GLOB:-artifacts/github-actions/*.json}"
TOP_N="${TOP_N:-20}"
OUTPUT_FORMAT="${OUTPUT_FORMAT:-text}"
MIN_RUNS="${MIN_RUNS:-2}"
EVENT_MATCH="${EVENT_MATCH:-^(pull_request|pull_request_target|merge_group)$}"
WORKFLOW_MATCH="${WORKFLOW_MATCH:-}"
WORKFLOW_EXCLUDE="${WORKFLOW_EXCLUDE:-}"
REPO_MATCH="${REPO_MATCH:-}"
REPO_EXCLUDE="${REPO_EXCLUDE:-}"
FAIL_WARN_PERCENT="${FAIL_WARN_PERCENT:-15}"
FAIL_CRITICAL_PERCENT="${FAIL_CRITICAL_PERCENT:-30}"
QUEUE_WARN_SECONDS="${QUEUE_WARN_SECONDS:-120}"
QUEUE_CRITICAL_SECONDS="${QUEUE_CRITICAL_SECONDS:-300}"
SUCCESS_STALE_DAYS="${SUCCESS_STALE_DAYS:-3}"
WARN_SCORE="${WARN_SCORE:-25}"
CRITICAL_SCORE="${CRITICAL_SCORE:-45}"
FAIL_ON_CRITICAL="${FAIL_ON_CRITICAL:-0}"

python3 - << PYEOF
import json, re, sys, os, glob
from datetime import datetime, timezone, timedelta
from pathlib import Path

run_glob       = os.environ.get("RUN_GLOB", "artifacts/github-actions/*.json")
top_n          = int(os.environ.get("TOP_N", "20"))
output_format  = os.environ.get("OUTPUT_FORMAT", "text")
min_runs       = int(os.environ.get("MIN_RUNS", "2"))
event_match    = os.environ.get("EVENT_MATCH", r"^(pull_request|pull_request_target|merge_group)$")
workflow_match   = os.environ.get("WORKFLOW_MATCH", "")
workflow_exclude = os.environ.get("WORKFLOW_EXCLUDE", "")
repo_match     = os.environ.get("REPO_MATCH", "")
repo_exclude   = os.environ.get("REPO_EXCLUDE", "")
fail_warn_pct  = float(os.environ.get("FAIL_WARN_PERCENT", "15"))
fail_crit_pct  = float(os.environ.get("FAIL_CRITICAL_PERCENT", "30"))
queue_warn_s   = float(os.environ.get("QUEUE_WARN_SECONDS", "120"))
queue_crit_s   = float(os.environ.get("QUEUE_CRITICAL_SECONDS", "300"))
stale_days     = float(os.environ.get("SUCCESS_STALE_DAYS", "3"))
warn_score     = float(os.environ.get("WARN_SCORE", "25"))
crit_score     = float(os.environ.get("CRITICAL_SCORE", "45"))
fail_on_crit   = os.environ.get("FAIL_ON_CRITICAL", "0") == "1"

def parse_dt(s):
    if not s:
        return None
    s = s.rstrip("Z")
    return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)

files = glob.glob(run_glob, recursive=True)
runs = []
for f in files:
    try:
        data = json.loads(Path(f).read_text())
        # handle both single run and list
        if isinstance(data, list):
            runs.extend(data)
        else:
            runs.append(data)
    except Exception:
        pass

# filter events
filtered = []
for r in runs:
    event = r.get("event", "")
    if not re.search(event_match, event):
        continue
    repo = ""
    repo_obj = r.get("repository", {})
    if isinstance(repo_obj, dict):
        repo = repo_obj.get("nameWithOwner", "")
    elif isinstance(repo_obj, str):
        repo = repo_obj
    workflow = r.get("workflowName", "")
    if workflow_match and not re.search(workflow_match, workflow):
        continue
    if workflow_exclude and re.search(workflow_exclude, workflow):
        continue
    if repo_match and not re.search(repo_match, repo):
        continue
    if repo_exclude and re.search(repo_exclude, repo):
        continue
    r["_repo"] = repo
    filtered.append(r)

# group
from collections import defaultdict
groups = defaultdict(list)
for r in filtered:
    key = (r["_repo"], r.get("workflowName",""), r.get("event",""))
    groups[key].append(r)

now = datetime.now(timezone.utc)

results = []
for (repo, workflow, event), grp in groups.items():
    if len(grp) < min_runs:
        continue
    total = len(grp)
    failures = sum(1 for r in grp if r.get("conclusion") in ("failure","timed_out","startup_failure"))
    fail_rate = failures / total * 100

    # consecutive current failures (sorted by createdAt desc)
    sorted_runs = sorted(grp, key=lambda r: r.get("createdAt",""), reverse=True)
    consec = 0
    for r in sorted_runs:
        if r.get("conclusion") in ("failure","timed_out","startup_failure"):
            consec += 1
        else:
            break

    # queue wait
    waits = []
    for r in grp:
        c = parse_dt(r.get("createdAt"))
        s = parse_dt(r.get("runStartedAt"))
        if c and s:
            w = (s - c).total_seconds()
            if w >= 0:
                waits.append(w)
    avg_queue = sum(waits)/len(waits) if waits else 0

    # stale success
    success_runs = [r for r in grp if r.get("conclusion") == "success"]
    if success_runs:
        last_success_dt = max(parse_dt(r.get("updatedAt","")) or now for r in success_runs)
        days_since = (now - last_success_dt).total_seconds() / 86400
    else:
        days_since = 9999

    # scoring
    score = 0
    # failure rate contribution
    if fail_rate >= fail_crit_pct:
        score += 30
    elif fail_rate >= fail_warn_pct:
        score += 15
    # consecutive failures
    score += min(consec * 5, 20)
    # queue wait
    if avg_queue >= queue_crit_s:
        score += 20
    elif avg_queue >= queue_warn_s:
        score += 10
    # stale success
    if days_since >= stale_days:
        score += 15

    if score >= crit_score:
        level = "critical"
    elif score >= warn_score:
        level = "warning"
    else:
        level = "ok"

    results.append({
        "repo": repo,
        "workflow": workflow,
        "event": event,
        "total_runs": total,
        "failures": failures,
        "fail_rate_percent": round(fail_rate, 1),
        "consecutive_failures": consec,
        "avg_queue_seconds": round(avg_queue, 1),
        "days_since_last_success": round(days_since, 2),
        "score": score,
        "level": level,
    })

results.sort(key=lambda x: x["score"], reverse=True)
results = results[:top_n]

critical_groups = [r for r in results if r["level"] == "critical"]
warning_groups  = [r for r in results if r["level"] == "warning"]
ok_groups       = [r for r in results if r["level"] == "ok"]

if output_format == "json":
    out = {
        "summary": {
            "total_groups": len(results),
            "critical": len(critical_groups),
            "warning": len(warning_groups),
            "ok": len(ok_groups),
        },
        "groups": results,
        "critical_details": critical_groups,
    }
    print(json.dumps(out, indent=2))
else:
    print("=== PR Gate Health Audit ===")
    print(f"Groups evaluated: {len(results)} | Critical: {len(critical_groups)} | Warning: {len(warning_groups)} | OK: {len(ok_groups)}")
    print()
    for r in results:
        print(f"[{r['level'].upper():8s}] score={r['score']:3d}  {r['repo']}  /  {r['workflow']}  ({r['event']})")
        print(f"           runs={r['total_runs']} failures={r['failures']} fail%={r['fail_rate_percent']} consec={r['consecutive_failures']} queue={r['avg_queue_seconds']}s stale={r['days_since_last_success']}d")

if fail_on_crit and critical_groups:
    sys.exit(1)
PYEOF
BASH_EOF

chmod +x "$SCRIPT_PATH"

echo "Setup complete. Skill script installed at $SCRIPT_PATH"
ls -la "$SKILL_DIR"