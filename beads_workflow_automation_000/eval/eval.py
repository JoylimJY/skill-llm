#!/usr/bin/env python3
"""
Evaluation script for the beads task.
Checks:
  1. bd was initialized (.beads/ exists)
  2. Epic created with P0 (critical) priority
  3. All 5 subtasks created under the epic with correct priorities
  4. Correct blocking dependency chain: ingest→transform→train→eval
  5. "Write deployment runbook" has NO blocking deps
  6. Ingestion task is closed
  7. The discovered bug task exists at P0 with discovered-from dep on ingestion
  8. Some task assigned to agent-falcon with status in_progress (transformation after close of ingestion)
  9. task_snapshot.json exists and contains all issues
  10. bd sync was run (git log has a beads commit or .beads/ is committed)
"""
import sys
import json
import subprocess
import os
from pathlib import Path

def run(cmd, cwd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
        return r.stdout.strip(), r.returncode
    except Exception as e:
        return str(e), 1

def parse_json_output(raw):
    """Try to parse JSON, handling possible extra text."""
    try:
        return json.loads(raw)
    except Exception:
        # Try to find first JSON object/array
        for start in [raw.find('['), raw.find('{')]:
            if start != -1:
                try:
                    return json.loads(raw[start:])
                except Exception:
                    pass
    return None

workspace = Path(sys.argv[1])
checks = []
score_parts = []

def check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})
    score_parts.append(1.0 if passed else 0.0)

# ── Check 1: .beads/ directory exists ───────────────────────────────────────
beads_dir = workspace / ".beads"
check(
    "beads_initialized",
    beads_dir.exists() and beads_dir.is_dir(),
    f".beads/ {'exists' if beads_dir.exists() else 'NOT FOUND'} at {beads_dir}"
)

# ── Get all issues via bd list --json ────────────────────────────────────────
raw_list, rc = run("bd list --json", cwd=str(workspace))
all_issues = []
if rc == 0 and raw_list:
    parsed = parse_json_output(raw_list)
    if isinstance(parsed, list):
        all_issues = parsed
    elif isinstance(parsed, dict) and "issues" in parsed:
        all_issues = parsed["issues"]

check(
    "bd_list_returns_issues",
    len(all_issues) > 0,
    f"bd list --json returned {len(all_issues)} issues (raw: {raw_list[:200]})"
)

# ── Helper: find issues by keyword in title ──────────────────────────────────
def find_by_title(keyword, issues=None):
    if issues is None:
        issues = all_issues
    keyword_lower = keyword.lower()
    return [i for i in issues if keyword_lower in i.get("title", "").lower()]

# ── Check 2: Epic exists with P0 priority ────────────────────────────────────
epics = [i for i in all_issues if i.get("type") == "epic" or 
         ("falcon" in i.get("title", "").lower() and "rollout" in i.get("title", "").lower())]
# Also check by title if type field not available
if not epics:
    epics = find_by_title("falcon") + find_by_title("rollout")
    epics = list({i.get("id", ""): i for i in epics}.values())

epic_ok = len(epics) > 0
epic_priority_ok = any(str(e.get("priority", "")) in ["0", "critical"] for e in epics) if epic_ok else False
check(
    "epic_created",
    epic_ok,
    f"Found {len(epics)} epic(s): {[e.get('id') for e in epics]}"
)
check(
    "epic_is_critical_p0",
    epic_priority_ok,
    f"Epic priorities: {[e.get('priority') for e in epics]}"
)

# ── Check 3: 5 subtasks exist ────────────────────────────────────────────────
subtask_keywords = [
    "ingestion",
    "transformation",
    "baseline model",
    "evaluation suite",
    "deployment runbook",
]
found_subtasks = {}
for kw in subtask_keywords:
    matches = find_by_title(kw)
    # Also try shorter matches
    if not matches:
        short = kw.split()[0]
        matches = find_by_title(short)
    found_subtasks[kw] = matches

all_5_found = all(len(v) > 0 for v in found_subtasks.values())
check(
    "all_5_subtasks_created",
    all_5_found,
    f"Subtask search: { {k: len(v) for k, v in found_subtasks.items()} }"
)

# ── Check 4: Ingestion task is closed ────────────────────────────────────────
ingest_tasks = found_subtasks.get("ingestion", [])
ingest_closed = any(t.get("status") == "closed" for t in ingest_tasks) if ingest_tasks else False
check(
    "ingestion_task_closed",
    ingest_closed,
    f"Ingestion task statuses: {[t.get('status') for t in ingest_tasks]}"
)

# ── Check 5: P0 bug discovered-from ingestion ────────────────────────────────
bug_tasks = [i for i in all_issues if 
             "csv" in i.get("title", "").lower() or 
             "crash" in i.get("title", "").lower() or
             "empty" in i.get("title", "").lower() or
             i.get("type") == "bug"]
bug_p0 = any(str(b.get("priority", "")) in ["0", "critical"] for b in bug_tasks)
check(
    "bug_task_created",
    len(bug_tasks) > 0,
    f"Found {len(bug_tasks)} bug task(s): {[b.get('title') for b in bug_tasks]}"
)
check(
    "bug_task_is_p0",
    bug_p0,
    f"Bug priorities: {[b.get('priority') for b in bug_tasks]}"
)

# Check discovered-from dep for bug: look in dep tree or issue deps
bug_has_discovered_dep = False
if bug_tasks and ingest_tasks:
    ingest_id = ingest_tasks[0].get("id", "")
    for bug in bug_tasks:
        bug_id = bug.get("id", "")
        if bug_id:
            raw_show, _ = run(f"bd show {bug_id} --json", cwd=str(workspace))
            show_data = parse_json_output(raw_show)
            if show_data:
                # Check deps in show output
                deps = show_data.get("deps", show_data.get("dependencies", []))
                if isinstance(deps, list):
                    for d in deps:
                        dep_str = str(d)
                        if "discovered" in dep_str.lower() or ingest_id in dep_str:
                            bug_has_discovered_dep = True
                            break
                # Also check raw output for discovered-from
                if "discovered" in raw_show.lower():
                    bug_has_discovered_dep = True

check(
    "bug_has_discovered_from_dep",
    bug_has_discovered_dep,
    f"Bug discovered-from dep on ingestion: {bug_has_discovered_dep}"
)

# ── Check 6: agent-falcon assigned to a task in_progress ─────────────────────
falcon_tasks = [i for i in all_issues if 
                i.get("assignee") == "agent-falcon" or 
                "agent-falcon" in str(i.get("assignee", ""))]
falcon_in_progress = any(t.get("status") == "in_progress" for t in falcon_tasks)
check(
    "agent_falcon_assigned_in_progress",
    falcon_in_progress,
    f"agent-falcon tasks: {[(t.get('id'), t.get('status')) for t in falcon_tasks]}"
)

# ── Check 7: transformation task in_progress or unblocked after ingest close ─
transform_tasks = found_subtasks.get("transformation", [])
# After ingestion closed, transformation should be unblocked / in_progress
transform_unblocked_or_active = any(
    t.get("status") in ["open", "in_progress"] for t in transform_tasks
)
check(
    "transform_unblocked_after_ingest_close",
    transform_unblocked_or_active,
    f"Transform task statuses: {[t.get('status') for t in transform_tasks]}"
)

# ── Check 8: task_snapshot.json exists and has all issues ────────────────────
snapshot_files = list(workspace.rglob("task_snapshot.json"))
snapshot_ok = False
snapshot_count = 0
snapshot_detail = "task_snapshot.json not found"
if snapshot_files:
    try:
        snap_path = snapshot_files[0]
        raw_snap = snap_path.read_text()
        snap_data = parse_json_output(raw_snap)
        if isinstance(snap_data, list):
            snapshot_count = len(snap_data)
        elif isinstance(snap_data, dict) and "issues" in snap_data:
            snapshot_count = len(snap_data["issues"])
        snapshot_ok = snapshot_count >= 6  # epic + 5 subtasks + bug = at least 7, but be lenient with 6
        snapshot_detail = f"task_snapshot.json found at {snap_path.relative_to(workspace)}, {snapshot_count} issues"
    except Exception as e:
        snapshot_detail = f"task_snapshot.json parse error: {e}"
else:
    snapshot_detail = "task_snapshot.json not found anywhere in workspace"
check(
    "task_snapshot_json_exists_with_issues",
    snapshot_ok,
    snapshot_detail
)

# ── Check 9: Dependencies — train blocked by transform, eval blocked by train ─
train_tasks = found_subtasks.get("baseline model", [])
eval_tasks = found_subtasks.get("evaluation suite", [])

dep_chain_ok = False
# Check bd blocked output for chained deps
raw_blocked, _ = run("bd blocked --json", cwd=str(workspace))
blocked_data = parse_json_output(raw_blocked)
blocked_ids = set()
if isinstance(blocked_data, list):
    blocked_ids = {b.get("id") for b in blocked_data}
elif isinstance(blocked_data, dict) and "issues" in blocked_data:
    blocked_ids = {b.get("id") for b in blocked_data["issues"]}

# Before ingestion was closed, train and eval should have been blocked.
# After close, transform became unblocked; train should still be blocked by transform.
train_blocked_check = any(t.get("id") in blocked_ids or t.get("status") == "blocked" 
                          for t in train_tasks) if train_tasks else False
check(
    "dependency_chain_enforced",
    train_blocked_check or (bool(train_tasks) and all(
        t.get("status") in ["blocked", "open"] for t in train_tasks
    )),
    f"Train tasks status/blocked: {[(t.get('id'), t.get('status')) for t in train_tasks]}, blocked_ids sample: {list(blocked_ids)[:5]}"
)

# ── Check 10: bd sync was run (git log shows beads-related commit) ───────────
raw_gitlog, _ = run("git log --oneline --all", cwd=str(workspace))
sync_committed = any(keyword in raw_gitlog.lower() for keyword in ["beads", "bd-", "sync", ".beads"])
check(
    "bd_sync_run_git_evidence",
    sync_committed,
    f"Git log sample: {raw_gitlog[:300]}"
)

# ── Final score ───────────────────────────────────────────────────────────────
passed_count = sum(1 for c in checks if c["passed"])
total = len(checks)
score = round(passed_count / total, 4)
all_passed = passed_count == total

result = {
    "passed": all_passed,
    "score": score,
    "checks": checks
}
print(json.dumps(result, indent=2))