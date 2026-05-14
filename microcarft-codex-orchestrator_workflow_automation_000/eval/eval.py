#!/usr/bin/env python3
"""
Evaluation script for the codex-orchestrator task.
Usage: python3 eval.py <workspace_dir>
"""
import sys
import os
import json
import glob
from pathlib import Path

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
STATE_DIR = "/tmp/codex_mock_state"

checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})
    print(f"  [{'PASS' if passed else 'FAIL'}] {name}: {detail}")

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 1: Was the PTY background launch invoked with correct proprietary syntax?
# ─────────────────────────────────────────────────────────────────────────────
try:
    launch_file = os.path.join(STATE_DIR, "launch_history.jsonl")
    if not os.path.exists(launch_file):
        add_check(
            "pty_background_launch",
            False,
            "No launch_history.jsonl found — bash pty:true background:true was never called."
        )
    else:
        launches = []
        with open(launch_file) as f:
            for line in f:
                line = line.strip()
                if line:
                    launches.append(json.loads(line))

        codex_launches = [
            l for l in launches
            if "codex" in l.get("command", "") and "exec" in l.get("command", "")
        ]
        if not codex_launches:
            add_check(
                "pty_background_launch",
                False,
                f"Found {len(launches)} launch(es) but none invoked 'codex exec'. Commands: {[l.get('command') for l in launches]}"
            )
        else:
            launch = codex_launches[0]
            pty_ok = launch.get("pty") is True
            bg_ok = launch.get("background") is True
            full_auto = "--full-auto" in launch.get("command", "")

            if pty_ok and bg_ok and full_auto:
                add_check(
                    "pty_background_launch",
                    True,
                    f"Correctly launched with pty:true background:true and --full-auto. workdir={launch.get('workdir')}"
                )
            else:
                add_check(
                    "pty_background_launch",
                    False,
                    f"Launch found but missing required flags. pty={pty_ok}, background={bg_ok}, full_auto={full_auto}. Raw: {launch}"
                )
except Exception as e:
    add_check("pty_background_launch", False, f"Exception: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 2: Was `process action:log` called to monitor progress?
# ─────────────────────────────────────────────────────────────────────────────
try:
    history_file = os.path.join(STATE_DIR, "action_history.jsonl")
    action_history = []
    if os.path.exists(history_file):
        with open(history_file) as f:
            for line in f:
                line = line.strip()
                if line:
                    action_history.append(json.loads(line))

    log_actions = [a for a in action_history if a.get("action") == "log"]
    if not log_actions:
        add_check(
            "monitored_via_log",
            False,
            "process action:log was never called. Agent did not monitor the session."
        )
    else:
        # Check limit parameter was used (any reasonable value)
        limits_used = [a.get("limit", 0) for a in log_actions]
        add_check(
            "monitored_via_log",
            True,
            f"process action:log called {len(log_actions)} time(s). Limits used: {limits_used}"
        )
except Exception as e:
    add_check("monitored_via_log", False, f"Exception: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 3: Was blockage detected and `process action:submit data:"y"` sent?
# ─────────────────────────────────────────────────────────────────────────────
try:
    submit_actions = [a for a in action_history if a.get("action") == "submit"]
    if not submit_actions:
        add_check(
            "blockage_resolved_via_submit",
            False,
            "process action:submit was never called. Agent failed to resolve interactive prompt blockage."
        )
    else:
        # Check that at least one submit had data "y" or "" (affirmative)
        affirmative_submits = [
            a for a in submit_actions
            if a.get("data", "").strip().lower() in ("y", "yes", "")
        ]
        if affirmative_submits:
            add_check(
                "blockage_resolved_via_submit",
                True,
                f"process action:submit called with affirmative data. Submits: {[a.get('data') for a in submit_actions]}"
            )
        else:
            add_check(
                "blockage_resolved_via_submit",
                False,
                f"submit was called but NOT with an affirmative response. Data sent: {[a.get('data') for a in submit_actions]}"
            )
except Exception as e:
    add_check("blockage_resolved_via_submit", False, f"Exception: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 4: Did the session reach "completed" state (not killed)?
# ─────────────────────────────────────────────────────────────────────────────
try:
    session_files = glob.glob(os.path.join(STATE_DIR, "????????.json"))
    sessions = []
    for sf in session_files:
        try:
            with open(sf) as f:
                sessions.append(json.load(f))
        except Exception:
            pass

    if not sessions:
        add_check(
            "session_completed_not_killed",
            False,
            "No session state files found. Codex was never launched."
        )
    else:
        completed = [s for s in sessions if s.get("phase") in ("completed", "completed_partial")]
        killed = [s for s in sessions if s.get("phase") == "killed"]

        if completed and not killed:
            add_check(
                "session_completed_not_killed",
                True,
                f"Session completed successfully (phase={completed[0].get('phase')}). {len(completed[0].get('files_changed', []))} files changed."
            )
        elif killed:
            add_check(
                "session_completed_not_killed",
                False,
                f"Session was killed instead of completed. Phases: {[s.get('phase') for s in sessions]}"
            )
        else:
            add_check(
                "session_completed_not_killed",
                False,
                f"Session never reached completed state. Phases: {[s.get('phase') for s in sessions]}"
            )
except Exception as e:
    add_check("session_completed_not_killed", False, f"Exception: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 5: Was a session_report.json produced with required fields?
# ─────────────────────────────────────────────────────────────────────────────
try:
    report_files = list(Path(workspace).rglob("session_report.json"))
    if not report_files:
        add_check(
            "session_report_produced",
            False,
            "session_report.json not found anywhere in the workspace."
        )
    else:
        report_path = report_files[0]
        with open(report_path) as f:
            report = json.load(f)

        required_fields = ["sessionId", "files_changed", "final_status"]
        missing = [field for field in required_fields if field not in report]

        if missing:
            add_check(
                "session_report_produced",
                False,
                f"session_report.json found at {report_path} but missing fields: {missing}. Report keys: {list(report.keys())}"
            )
        else:
            # Validate content quality
            sid_ok = bool(report.get("sessionId", "").strip())
            files_ok = isinstance(report.get("files_changed"), list) and len(report.get("files_changed", [])) > 0
            status_ok = bool(report.get("final_status", "").strip())

            if sid_ok and files_ok and status_ok:
                add_check(
                    "session_report_produced",
                    True,
                    f"Valid session_report.json at {report_path}. sessionId={report['sessionId']}, "
                    f"files_changed={len(report['files_changed'])}, final_status={report['final_status']}"
                )
            else:
                add_check(
                    "session_report_produced",
                    False,
                    f"session_report.json has empty/invalid fields. "
                    f"sessionId_ok={sid_ok}, files_ok={files_ok}, status_ok={status_ok}. Content: {report}"
                )
except json.JSONDecodeError as e:
    add_check("session_report_produced", False, f"session_report.json is not valid JSON: {e}")
except Exception as e:
    add_check("session_report_produced", False, f"Exception reading session_report.json: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 6: Session IDs are consistent (log/submit used same session as launched)
# ─────────────────────────────────────────────────────────────────────────────
try:
    # Get session IDs from action history
    if action_history and sessions:
        # Collect all sessionIds from submit and log actions
        action_sids = set(a.get("sessionId", "") for a in action_history if a.get("sessionId"))
        # Collect session IDs from actual sessions
        real_sids = set(s.get("sessionId", "") for s in sessions)

        orphaned_actions = action_sids - real_sids
        if orphaned_actions:
            add_check(
                "session_id_consistency",
                False,
                f"Actions were performed on non-existent session IDs: {orphaned_actions}"
            )
        else:
            add_check(
                "session_id_consistency",
                True,
                f"All actions used valid session IDs. Sessions: {real_sids}, Action session refs: {action_sids}"
            )
    else:
        add_check(
            "session_id_consistency",
            len(action_history) == 0,
            "No action history or no sessions to cross-check."
        )
except Exception as e:
    add_check("session_id_consistency", False, f"Exception: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# Scoring
# ─────────────────────────────────────────────────────────────────────────────
# Weights: launch(2), monitor(1), submit(2), completed(2), report(2), consistency(1) = 10 total
weights = {
    "pty_background_launch": 2,
    "monitored_via_log": 1,
    "blockage_resolved_via_submit": 2,
    "session_completed_not_killed": 2,
    "session_report_produced": 2,
    "session_id_consistency": 1,
}
total_weight = sum(weights.values())
earned = sum(weights[c["name"]] for c in checks if c["passed"] and c["name"] in weights)
score = round(earned / total_weight, 4)

all_passed = all(c["passed"] for c in checks)

result = {
    "passed": all_passed,
    "score": score,
    "checks": checks,
}
print("\n" + json.dumps(result, indent=2))