#!/usr/bin/env python3
"""
Evaluation script for the antfarm bug-fix workflow task.
Checks that the agent:
  1. Installed antfarm correctly (INSTALLED_FLAG exists)
  2. Started a bug-fix workflow run with a well-formed task string (specific problem, tech details, acceptance criteria)
  3. Force-triggered the first-step cron using the correct job-ID pattern antfarm/bug-fix/<agent>
  4. Produced bug_run_report.json containing run_id, workflow, status, and current_step
"""

import sys
import json
import os
import pathlib

workspace = sys.argv[1]
HOME = os.path.expanduser("~")
STATE_DIR = os.path.join(HOME, ".openclaw", "antfarm-state")

checks = []
score_weights = []  # (weight, passed)

def make_check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})

# ── Check 1: antfarm was installed ───────────────────────────────────────────
try:
    installed_flag = os.path.join(STATE_DIR, "installed")
    flag_exists = os.path.exists(installed_flag)
    make_check(
        "antfarm_installed",
        flag_exists,
        "installed flag found" if flag_exists else f"installed flag missing at {installed_flag}"
    )
    score_weights.append((0.15, flag_exists))
except Exception as e:
    make_check("antfarm_installed", False, f"Exception: {e}")
    score_weights.append((0.15, False))

# ── Check 2: A bug-fix workflow run was created ───────────────────────────────
runs = []
bug_fix_run = None
try:
    runs_file = os.path.join(STATE_DIR, "runs.json")
    with open(runs_file) as f:
        runs = json.load(f)
    bug_fix_runs = [r for r in runs if r.get("workflow") == "bug-fix"]
    bug_fix_run = bug_fix_runs[0] if bug_fix_runs else None
    passed = bug_fix_run is not None
    make_check(
        "bug_fix_run_created",
        passed,
        f"Found {len(bug_fix_runs)} bug-fix run(s)" if passed else "No bug-fix workflow run found in runs.json"
    )
    score_weights.append((0.20, passed))
except Exception as e:
    make_check("bug_fix_run_created", False, f"Exception reading runs.json: {e}")
    score_weights.append((0.20, False))

# ── Check 3: Task string is substantive (has problem + tech details + acceptance criteria) ───
try:
    if bug_fix_run:
        task = bug_fix_run.get("task", "")
        # Must be meaningful — not just a few words
        has_length    = len(task) >= 80
        # Must reference the auth/JWT/concurrent bug context
        has_bug_ref   = any(kw in task.lower() for kw in ["auth", "jwt", "concurrent", "race", "token", "middleware", "payment"])
        # Must have acceptance criteria signals (checkboxes or bullet criteria)
        has_criteria  = any(kw in task.lower() for kw in ["criteria", "accept", "[ ]", "must", "should", "verify", "test"])
        passed = has_length and has_bug_ref and has_criteria
        detail = (
            f"length={len(task)}, has_bug_ref={has_bug_ref}, has_criteria={has_criteria}. "
            f"Task snippet: {task[:120]!r}"
        )
    else:
        passed = False
        detail = "No bug-fix run to inspect task string"
    make_check("task_string_well_formed", passed, detail)
    score_weights.append((0.20, passed))
except Exception as e:
    make_check("task_string_well_formed", False, f"Exception: {e}")
    score_weights.append((0.20, False))

# ── Check 4: Cron was force-triggered for the triage agent ──────────────────
# Evidence: triage step is NOT "pending" anymore (it's completed/in-progress)
# AND crons.json shows lastRun set for antfarm/bug-fix/triage
try:
    crons_file = os.path.join(STATE_DIR, "crons.json")
    with open(crons_file) as f:
        crons = json.load(f)
    triage_cron = next((c for c in crons if c.get("id") == "antfarm/bug-fix/triage"), None)
    if triage_cron is None:
        # Also accept investigator being triggered (triage already done, next step triggered)
        triage_cron = next((c for c in crons if c.get("id", "").startswith("antfarm/bug-fix/")), None)
    cron_triggered = triage_cron is not None and triage_cron.get("lastRun") is not None
    # Also check steps
    steps_file = os.path.join(STATE_DIR, "steps.json")
    with open(steps_file) as f:
        steps = json.load(f)
    triage_step_done = any(
        s.get("agent") == "triage" and s.get("status") in ("completed", "in-progress")
        for s in steps
    )
    passed = cron_triggered or triage_step_done
    detail = (
        f"cron_triggered={cron_triggered} (lastRun={triage_cron.get('lastRun') if triage_cron else 'N/A'}), "
        f"triage_step_done={triage_step_done}"
    )
    make_check("cron_force_triggered", passed, detail)
    score_weights.append((0.25, passed))
except Exception as e:
    make_check("cron_force_triggered", False, f"Exception: {e}")
    score_weights.append((0.25, False))

# ── Check 5: bug_run_report.json exists and has required fields ──────────────
try:
    report_paths = list(pathlib.Path(workspace).rglob("bug_run_report.json"))
    if not report_paths:
        make_check("bug_run_report_exists", False, "bug_run_report.json not found anywhere in workspace")
        score_weights.append((0.20, False))
    else:
        report_path = report_paths[0]
        with open(report_path) as f:
            report = json.load(f)

        has_run_id   = "run_id" in report or "runId" in report or "id" in report
        has_workflow = any(k in report for k in ("workflow", "workflow_id", "workflowId"))
        has_status   = "status" in report
        # run_id value must match a real run
        run_id_val = report.get("run_id") or report.get("runId") or report.get("id", "")
        run_id_valid = any(r.get("id", "").startswith(str(run_id_val)[:5]) for r in runs) if runs and run_id_val else False

        passed = has_run_id and has_workflow and has_status
        detail = (
            f"path={report_path}, has_run_id={has_run_id}, has_workflow={has_workflow}, "
            f"has_status={has_status}, run_id_valid={run_id_valid}. "
            f"Keys: {list(report.keys())}"
        )
        make_check("bug_run_report_valid", passed, detail)
        score_weights.append((0.20, passed))

        # Bonus: run_id in report matches actual run
        make_check(
            "bug_run_report_run_id_correct",
            run_id_valid,
            f"run_id={run_id_val!r}, matched={run_id_valid}"
        )
        # No extra weight — sub-check for detail
except Exception as e:
    make_check("bug_run_report_exists", False, f"Exception: {e}")
    score_weights.append((0.20, False))

# ── Final score ──────────────────────────────────────────────────────────────
total_weight = sum(w for w, _ in score_weights)
earned       = sum(w for w, p in score_weights if p)
score        = round(earned / total_weight, 4) if total_weight > 0 else 0.0
passed_overall = score >= 0.75

result = {
    "passed": passed_overall,
    "score":  score,
    "checks": checks,
}
print(json.dumps(result, indent=2))