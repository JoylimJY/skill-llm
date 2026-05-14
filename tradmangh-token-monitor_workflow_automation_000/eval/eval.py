#!/usr/bin/env python3
"""
Evaluation script for the token-monitor task.
Usage: python3 eval_script.py /workspace
"""

import sys
import json
import os
import subprocess
from pathlib import Path

def run_check(name, fn):
    try:
        passed, detail = fn()
        return {"name": name, "passed": passed, "detail": detail}
    except Exception as e:
        return {"name": name, "passed": False, "detail": f"Exception: {e}"}


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []

    # ── Paths ─────────────────────────────────────────────────────────────────
    state_file_default = Path(workspace) / ".openclaw/workspace/skills/token-monitor/.token-state.json"
    snapshot1 = str(Path(workspace) / ".openclaw/bin/snapshot1.txt")
    snapshot2 = str(Path(workspace) / ".openclaw/bin/snapshot2.txt")
    wake_log = Path(workspace) / ".openclaw/bin/wake.log"
    script = str(Path(workspace) / "skills/token-monitor/scripts/check-quota.sh")

    custom_threshold = "15"
    custom_state = str(Path(workspace) / ".openclaw/workspace/skills/token-monitor/.token-state.json")

    env_base = {
        **os.environ,
        "PATH": f"{Path(workspace)/'.openclaw/bin'}:/usr/local/bin:/usr/bin:/bin",
        "OPENCLAW_WAKE_LOG": str(wake_log),
        "HOME": str(Path(workspace)),
    }

    # ─────────────────────────────────────────────────────────────────────────
    # RUN 1: First invocation with custom threshold 15, snapshot1
    # Expected: 3 alerts (openai-codex 5h:8%, github-copilot Premium:3%, google-antigravity Premium:19%)
    # ─────────────────────────────────────────────────────────────────────────

    # Clean state
    if state_file_default.exists():
        state_file_default.unlink()
    if wake_log.exists():
        wake_log.unlink()

    env_run1 = {**env_base, "OPENCLAW_SNAPSHOT": snapshot1}
    run1_result = subprocess.run(
        ["bash", script, "--threshold", custom_threshold, "--state-file", custom_state],
        capture_output=True, text=True, cwd=workspace, env=env_run1
    )

    # CHECK 1: Script exits successfully
    def check_run1_exit():
        if run1_result.returncode == 0:
            return True, f"Script exited with code 0. stdout={run1_result.stdout[:200]}"
        return False, f"Script exited with code {run1_result.returncode}. stderr={run1_result.stderr[:300]}"
    checks.append(run_check("run1_script_exit_success", check_run1_exit))

    # CHECK 2: State file created
    def check_state_file_exists():
        if state_file_default.exists():
            return True, f"State file found at {state_file_default}"
        return False, f"State file NOT found at {state_file_default}"
    checks.append(run_check("run1_state_file_created", check_state_file_exists))

    # CHECK 3: State file valid JSON with required keys
    state1 = None
    def check_state_valid_json():
        nonlocal state1
        try:
            with open(state_file_default) as f:
                state1 = json.load(f)
            required = {"warned", "current", "lastCheck", "threshold"}
            missing = required - set(state1.keys())
            if missing:
                return False, f"State file missing keys: {missing}. Got: {list(state1.keys())}"
            return True, f"State file has all required keys: {list(state1.keys())}"
        except Exception as e:
            return False, f"Could not parse state file: {e}"
    checks.append(run_check("run1_state_valid_json", check_state_valid_json))

    # Load state if not already loaded
    if state1 is None:
        try:
            with open(state_file_default) as f:
                state1 = json.load(f)
        except:
            state1 = {}

    # CHECK 4: threshold stored correctly (15, not 20)
    def check_state_threshold():
        t = state1.get("threshold")
        if t == 15:
            return True, f"threshold={t} (correct)"
        return False, f"threshold={t} (expected 15, the custom value passed via --threshold)"
    checks.append(run_check("run1_state_threshold_correct", check_state_threshold))

    # CHECK 5: warned array contains exactly the 3 low-quota items (all below 15%)
    # With threshold=15: openai-codex 5h=8% (LOW), github-copilot Premium=3% (LOW)
    # google-antigravity Premium=19% is NOT below 15, so not warned
    def check_state_warned_run1():
        warned = state1.get("warned", [])
        expected_low = {"openai-codex 5h: 8% left", "github-copilot Premium: 3% left"}
        # google-antigravity Premium: 19% is above 15%, should NOT be in warned
        unexpected = {"google-antigravity Premium: 19% left"}
        warned_set = set(warned)
        missing = expected_low - warned_set
        present_unexpected = unexpected & warned_set
        if missing:
            return False, f"Missing from warned: {missing}. Got warned: {warned}"
        if present_unexpected:
            return False, f"Unexpected items in warned (above threshold=15): {present_unexpected}. Got: {warned}"
        return True, f"warned contains correct items: {warned}"
    checks.append(run_check("run1_state_warned_correct", check_state_warned_run1))

    # CHECK 6: current array contains ALL quota entries in provider:quota=pct format
    def check_state_current_run1():
        current = state1.get("current", [])
        expected_entries = {
            "openai-codex:5h=8",
            "openai-codex:Day=55",
            "github-copilot:Premium=3",
            "github-copilot:Chat=72",
            "google-antigravity:Day=100",
            "google-antigravity:Premium=19",
        }
        current_set = set(current)
        missing = expected_entries - current_set
        if missing:
            return False, f"Missing from current: {missing}. Got current: {current}"
        return True, f"current has all {len(expected_entries)} quota entries"
    checks.append(run_check("run1_state_current_complete", check_state_current_run1))

    # CHECK 7: alert was emitted (stdout or wake log contains the warning)
    def check_run1_alert_emitted():
        output = run1_result.stdout + (wake_log.read_text() if wake_log.exists() else "")
        if "⚠️" in output or "Model Quota Alert" in output:
            return True, f"Alert found in output/wake log"
        return False, f"No ⚠️ alert found. stdout={run1_result.stdout[:300]}, wake_log={'(missing)' if not wake_log.exists() else wake_log.read_text()[:300]}"
    checks.append(run_check("run1_alert_emitted", check_run1_alert_emitted))

    # CHECK 8: No recovery alert on first run (nothing to recover from)
    def check_run1_no_recovery():
        output = run1_result.stdout + (wake_log.read_text() if wake_log.exists() else "")
        if "✅" in output or "Quota Recovered" in output:
            return False, f"Unexpected recovery alert on first run: {output[:300]}"
        return True, "No spurious recovery alert on first run"
    checks.append(run_check("run1_no_spurious_recovery", check_run1_no_recovery))

    # ─────────────────────────────────────────────────────────────────────────
    # RUN 2: Second invocation with same threshold=15, snapshot2
    # Snapshot2: openai-codex 5h=45% (RECOVERED), openai-codex Day=10% (NEW LOW)
    #            github-copilot Premium=3% (still low, already warned)
    #            google-antigravity Premium=19% (above 15%, same as before)
    # Expected:
    #   - Recovery alert: openai-codex 5h (was warned, now 45% >= 15%)
    #   - New warning alert: openai-codex Day: 10% left (new, below 15%)
    #   - NO re-alert for github-copilot Premium (already in warned)
    # ─────────────────────────────────────────────────────────────────────────

    if wake_log.exists():
        wake_log.unlink()

    env_run2 = {**env_base, "OPENCLAW_SNAPSHOT": snapshot2}
    run2_result = subprocess.run(
        ["bash", script, "--threshold", custom_threshold, "--state-file", custom_state],
        capture_output=True, text=True, cwd=workspace, env=env_run2
    )

    # CHECK 9: Script exits successfully on second run
    def check_run2_exit():
        if run2_result.returncode == 0:
            return True, f"Run2 script exited code 0"
        return False, f"Run2 script exited code {run2_result.returncode}. stderr={run2_result.stderr[:300]}"
    checks.append(run_check("run2_script_exit_success", check_run2_exit))

    # Load state after run2
    state2 = {}
    try:
        with open(state_file_default) as f:
            state2 = json.load(f)
    except Exception as e:
        checks.append({"name": "run2_state_load", "passed": False, "detail": f"Could not load state after run2: {e}"})

    # CHECK 10: Recovery alert emitted for openai-codex 5h
    def check_run2_recovery_alert():
        output = run2_result.stdout + (wake_log.read_text() if wake_log.exists() else "")
        if ("✅" in output or "Quota Recovered" in output) and "openai-codex" in output and ("5h" in output):
            return True, f"Recovery alert found for openai-codex 5h"
        return False, f"No recovery alert for openai-codex 5h. output={output[:400]}"
    checks.append(run_check("run2_recovery_alert_emitted", check_run2_recovery_alert))

    # CHECK 11: New warning alert emitted for openai-codex Day
    def check_run2_new_warning():
        output = run2_result.stdout + (wake_log.read_text() if wake_log.exists() else "")
        if ("⚠️" in output or "Model Quota Alert" in output) and "openai-codex" in output and "Day" in output:
            return True, f"New warning alert found for openai-codex Day"
        return False, f"No new warning for openai-codex Day. output={output[:400]}"
    checks.append(run_check("run2_new_warning_emitted", check_run2_new_warning))

    # CHECK 12: No duplicate alert for github-copilot Premium (already warned)
    def check_run2_no_duplicate():
        # The NEW_WARNINGS list should not include github-copilot Premium (already in prev warned)
        # We verify by checking that the warned array in state2 still contains it but it wasn't
        # re-emitted as a NEW warning. Since we can't easily distinguish from output alone,
        # we check that github-copilot Premium is still in state2.warned (not lost) but
        # wasn't added twice.
        warned2 = state2.get("warned", [])
        cop_count = sum(1 for w in warned2 if "github-copilot" in w and "Premium" in w)
        if cop_count == 1:
            return True, f"github-copilot Premium appears exactly once in warned: {warned2}"
        elif cop_count == 0:
            return False, f"github-copilot Premium missing from warned (should still be low). warned={warned2}"
        else:
            return False, f"github-copilot Premium duplicated in warned ({cop_count} times): {warned2}"
    checks.append(run_check("run2_no_duplicate_in_warned", check_run2_no_duplicate))

    # CHECK 13: State2 warned contains openai-codex Day (new), github-copilot Premium (carried over)
    # and does NOT contain openai-codex 5h (recovered)
    def check_run2_warned_final():
        warned2 = state2.get("warned", [])
        warned_set = set(warned2)
        should_have = {"openai-codex Day: 10% left", "github-copilot Premium: 3% left"}
        should_not_have = {"openai-codex 5h: 8% left"}  # recovered
        missing = should_have - warned_set
        wrongly_present = should_not_have & warned_set
        if missing:
            return False, f"Missing from warned after run2: {missing}. Got: {warned2}"
        if wrongly_present:
            return False, f"Recovered item still in warned: {wrongly_present}. Got: {warned2}"
        return True, f"warned after run2 is correct: {warned2}"
    checks.append(run_check("run2_warned_final_correct", check_run2_warned_final))

    # CHECK 14: State2 current reflects snapshot2 values
    def check_run2_current():
        current2 = state2.get("current", [])
        expected = {
            "openai-codex:5h=45",
            "openai-codex:Day=10",
            "github-copilot:Premium=3",
            "github-copilot:Chat=72",
            "google-antigravity:Day=100",
            "google-antigravity:Premium=19",
        }
        current_set = set(current2)
        missing = expected - current_set
        if missing:
            return False, f"Missing from current after run2: {missing}. Got: {current2}"
        # ensure old value is gone
        if "openai-codex:5h=8" in current_set:
            return False, f"Old value 'openai-codex:5h=8' still present in current after run2"
        return True, f"current after run2 reflects snapshot2 correctly"
    checks.append(run_check("run2_current_updated", check_run2_current))

    # ── Scoring ───────────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4) if total > 0 else 0.0
    overall_passed = passed_count == total

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks,
    }
    print(json.dumps(result, indent=2))
    return 0 if overall_passed else 1


if __name__ == "__main__":
    sys.exit(main())