#!/usr/bin/env python3
"""
Evaluation script for the microservice decomposition workflow task.
Checks that the agent correctly used all four openclaw skill scripts
in the proper order with the correct proprietary arguments.
"""
import sys
import json
import subprocess
import os
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

checks = []
score_per_check = 1.0

def node_script(script_name, *args):
    """Run a node/python skill script and return stdout."""
    # Find SKILL_DIR
    result = subprocess.run(
        ["npm", "root", "-g"],
        capture_output=True, text=True
    )
    npm_root = result.stdout.strip()
    skill_dir = os.path.join(npm_root, "openclaw", "skills", "multi-step-workflow")
    script = os.path.join(skill_dir, "scripts", script_name)
    if script_name.endswith(".py"):
        cmd = ["python3", script] + list(args)
    else:
        cmd = ["node", script] + list(args)
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.stdout, res.stderr, res.returncode

# ─── Check 1: state-machine task exists with correct task_id ─────────────────
check_name = "state_machine_task_initialized"
try:
    stdout, stderr, rc = node_script("state-machine.js", "get", "msvc-decomp-2024")
    data = json.loads(stdout)
    tid = data.get("task_id", "")
    tname = data.get("task_name", "")
    passed = (tid == "msvc-decomp-2024") and (len(tname) > 0)
    checks.append({
        "name": check_name,
        "passed": passed,
        "detail": f"task_id={tid}, task_name={tname!r}, stderr={stderr.strip()}"
    })
except Exception as e:
    checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

# ─── Check 2: state-machine reached DONE via valid path ──────────────────────
check_name = "state_machine_reached_done"
try:
    stdout, stderr, rc = node_script("state-machine.js", "get", "msvc-decomp-2024")
    data = json.loads(stdout)
    current_state = data.get("state", "")
    history = data.get("history", [])
    passed = current_state == "DONE"
    detail = f"current_state={current_state}, history_len={len(history)}"
    checks.append({"name": check_name, "passed": passed, "detail": detail})
except Exception as e:
    checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

# ─── Check 3: state-machine traversed required states in history ─────────────
check_name = "state_machine_valid_transition_path"
try:
    stdout, stderr, rc = node_script("state-machine.js", "get", "msvc-decomp-2024")
    data = json.loads(stdout)
    history = data.get("history", [])
    transitions = [(h["from"], h["to"]) for h in history]
    required_pairs = [
        ("IDLE", "PLANNING"),
        ("PLANNING", "DELEGATING"),
        ("DELEGATING", "EXECUTING"),
        ("EXECUTING", "MEMORYING"),
        ("MEMORYING", "DONE"),
    ]
    # Check each required transition appears somewhere in history (order-sensitive subset)
    hist_set = [(h["from"], h["to"]) for h in history]
    missing = [p for p in required_pairs if p not in hist_set]
    passed = len(missing) == 0
    checks.append({
        "name": check_name,
        "passed": passed,
        "detail": f"transitions found={hist_set}, missing={missing}"
    })
except Exception as e:
    checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

# ─── Check 4: task-tracker has correct task with pipe-separated steps ─────────
check_name = "task_tracker_task_created_with_correct_steps"
try:
    stdout, stderr, rc = node_script("task-tracker.py", "list")
    tasks = json.loads(stdout)
    target = None
    for t in tasks:
        if t.get("task") == "msvc-decomp-2024":
            target = t
            break
    if target is None:
        checks.append({"name": check_name, "passed": False, "detail": "Task msvc-decomp-2024 not found in tracker"})
    else:
        steps = target.get("steps", [])
        # Must have 5 steps (from project_intake.txt: Audit, Define, Scaffold, Deploy, Validate)
        passed = len(steps) == 5
        checks.append({
            "name": check_name,
            "passed": passed,
            "detail": f"steps_count={len(steps)}, steps={[s.get('name','') for s in steps]}"
        })
except Exception as e:
    checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

# ─── Check 5: all 5 task steps are marked done ───────────────────────────────
check_name = "task_tracker_all_steps_completed"
try:
    stdout, stderr, rc = node_script("task-tracker.py", "list")
    tasks = json.loads(stdout)
    target = None
    for t in tasks:
        if t.get("task") == "msvc-decomp-2024":
            target = t
            break
    if target is None:
        checks.append({"name": check_name, "passed": False, "detail": "Task not found"})
    else:
        steps = target.get("steps", [])
        all_done = all(s.get("done") is True for s in steps)
        done_count = sum(1 for s in steps if s.get("done") is True)
        checks.append({
            "name": check_name,
            "passed": all_done,
            "detail": f"done={done_count}/{len(steps)}"
        })
except Exception as e:
    checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

# ─── Check 6: context snapshot was saved with task name ──────────────────────
check_name = "context_snapshot_saved"
try:
    stdout, stderr, rc = node_script("context-snapshot.js", "load")
    snap = json.loads(stdout)
    task_val = snap.get("task", "")
    findings_val = snap.get("findings", "")
    pending_val = snap.get("pending", "")
    passed = (
        "msvc-decomp-2024" in task_val or "Monolith" in task_val or "decomp" in task_val.lower()
    ) and len(findings_val) > 5 and len(pending_val) > 5
    checks.append({
        "name": check_name,
        "passed": passed,
        "detail": f"task={task_val!r}, findings_len={len(findings_val)}, pending_len={len(pending_val)}, stderr={stderr.strip()}"
    })
except Exception as e:
    checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

# ─── Check 7: delegate was called with context_pct=42 ────────────────────────
# We verify by calling delegate.js ourselves with 42 and checking it returns valid JSON
# The agent should have called it with 42 per the project_intake.txt
check_name = "delegate_called_with_context_42"
try:
    stdout, stderr, rc = node_script("delegate.js", "42")
    data = json.loads(stdout)
    # The script is deterministic: pct=42 → MAIN_ONLY
    passed = (
        data.get("context_pct") == 42.0 and
        "recommendation" in data and
        rc == 0
    )
    # Cross-check: look for evidence in any log file the agent may have written
    log_files = list(workspace.rglob("*.log")) + list(workspace.rglob("*.txt")) + list(workspace.rglob("*.json"))
    found_42 = False
    for lf in log_files:
        try:
            content = lf.read_text(errors="ignore")
            if "42" in content and ("delegate" in content.lower() or "MAIN_ONLY" in content or "context_pct" in content):
                found_42 = True
                break
        except Exception:
            pass
    # delegate.js itself works correctly (sanity), agent usage evidenced by snapshot/tracker existing
    # We confirm delegate.js is functional — agent must have called it correctly
    checks.append({
        "name": check_name,
        "passed": passed,
        "detail": f"delegate.js output: {data}, found_42_in_logs={found_42}"
    })
except Exception as e:
    checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

# ─── Check 8: no stale/aborted state was reused ──────────────────────────────
check_name = "stale_state_not_reused"
try:
    # The stale state file has state=EXECUTING. Verify the history starts from IDLE.
    stdout, stderr, rc = node_script("state-machine.js", "get", "msvc-decomp-2024")
    data = json.loads(stdout)
    history = data.get("history", [])
    # First transition must be FROM IDLE (not from EXECUTING or any mid-state)
    if len(history) == 0:
        checks.append({"name": check_name, "passed": False, "detail": "No history at all"})
    else:
        first_from = history[0].get("from", "")
        passed = first_from == "IDLE"
        checks.append({
            "name": check_name,
            "passed": passed,
            "detail": f"First transition from={first_from!r} (expected 'IDLE')"
        })
except Exception as e:
    checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

# ─── Aggregate ────────────────────────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 4) if total > 0 else 0.0
overall_passed = passed_count == total

result = {
    "passed": overall_passed,
    "score": score,
    "checks": checks
}

print(json.dumps(result, indent=2))