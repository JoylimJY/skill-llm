import sys
import json
from pathlib import Path

def load_json(path):
    with open(path) as f:
        return json.load(f)

def run_checks(workspace_dir):
    ws = Path(workspace_dir)
    config_path = ws / "config" / "presence.json"
    state_path  = ws / "config" / "state.json"

    checks = []
    overall_passed = True

    # ── CHECK 1: Config file exists ───────────────────────────────────────────
    try:
        cfg = load_json(config_path)
        checks.append({"name": "config_file_exists", "passed": True,
                        "detail": f"presence.json found: {cfg}"})
    except Exception as e:
        checks.append({"name": "config_file_exists", "passed": False,
                        "detail": f"Could not read presence.json: {e}"})
        overall_passed = False
        # Can't continue meaningfully without config
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    # ── CHECK 2: Letter is 'R' ────────────────────────────────────────────────
    try:
        letter = cfg.get("letter", "")
        passed = (letter == "R")
        checks.append({"name": "config_letter_is_R", "passed": passed,
                        "detail": f"Expected letter='R', got '{letter}'"})
        if not passed:
            overall_passed = False
    except Exception as e:
        checks.append({"name": "config_letter_is_R", "passed": False,
                        "detail": f"Exception: {e}"})
        overall_passed = False

    # ── CHECK 3: Name is 'RESEARCHER' ─────────────────────────────────────────
    try:
        name = cfg.get("name", "")
        passed = (name == "RESEARCHER")
        checks.append({"name": "config_name_is_RESEARCHER", "passed": passed,
                        "detail": f"Expected name='RESEARCHER', got '{name}'"})
        if not passed:
            overall_passed = False
    except Exception as e:
        checks.append({"name": "config_name_is_RESEARCHER", "passed": False,
                        "detail": f"Exception: {e}"})
        overall_passed = False

    # ── CHECK 4: Timeout is 0 (auto-idle disabled) ────────────────────────────
    try:
        timeout = cfg.get("timeout", -1)
        passed = (timeout == 0)
        checks.append({"name": "config_timeout_disabled", "passed": passed,
                        "detail": f"Expected timeout=0 (disabled), got '{timeout}'"})
        if not passed:
            overall_passed = False
    except Exception as e:
        checks.append({"name": "config_timeout_disabled", "passed": False,
                        "detail": f"Exception: {e}"})
        overall_passed = False

    # ── CHECK 5: State file exists ────────────────────────────────────────────
    try:
        state = load_json(state_path)
        checks.append({"name": "state_file_exists", "passed": True,
                        "detail": f"state.json found: {state}"})
    except Exception as e:
        checks.append({"name": "state_file_exists", "passed": False,
                        "detail": f"Could not read state.json: {e}"})
        overall_passed = False
        score = sum(1 for c in checks if c["passed"]) / len(checks)
        print(json.dumps({"passed": False, "score": round(score, 2), "checks": checks}))
        return

    # ── CHECK 6: Final state is 'sleep' ───────────────────────────────────────
    try:
        final_state = state.get("state", "")
        passed = (final_state == "sleep")
        checks.append({"name": "final_state_is_sleep", "passed": passed,
                        "detail": f"Expected final state='sleep', got '{final_state}'"})
        if not passed:
            overall_passed = False
    except Exception as e:
        checks.append({"name": "final_state_is_sleep", "passed": False,
                        "detail": f"Exception: {e}"})
        overall_passed = False

    # ── CHECK 7: sleep state has NO activity text (proprietary trap) ──────────
    try:
        activity = state.get("activity", None)
        passed = (activity is None)
        checks.append({"name": "sleep_has_no_activity_text", "passed": passed,
                        "detail": f"sleep state must have null activity; got '{activity}'"})
        if not passed:
            overall_passed = False
    except Exception as e:
        checks.append({"name": "sleep_has_no_activity_text", "passed": False,
                        "detail": f"Exception: {e}"})
        overall_passed = False

    # ── CHECK 8: State reflects correct agent identity (R / RESEARCHER) ───────
    try:
        agent_letter = state.get("agent_letter", "")
        agent_name   = state.get("agent_name", "")
        passed = (agent_letter == "R" and agent_name == "RESEARCHER")
        checks.append({"name": "state_reflects_correct_identity", "passed": passed,
                        "detail": f"Expected letter=R name=RESEARCHER in state; got letter='{agent_letter}' name='{agent_name}'"})
        if not passed:
            overall_passed = False
    except Exception as e:
        checks.append({"name": "state_reflects_correct_identity", "passed": False,
                        "detail": f"Exception: {e}"})
        overall_passed = False

    # ── CHECK 9: Color for sleep state is 'blue' ──────────────────────────────
    try:
        color = state.get("color", "")
        passed = (color == "blue")
        checks.append({"name": "sleep_state_color_is_blue", "passed": passed,
                        "detail": f"Expected color='blue' for sleep, got '{color}'"})
        if not passed:
            overall_passed = False
    except Exception as e:
        checks.append({"name": "sleep_state_color_is_blue", "passed": False,
                        "detail": f"Exception: {e}"})
        overall_passed = False

    # ── CHECK 10: Stale config fields removed (letter no longer X/OLDBOT) ─────
    try:
        stale_letter = cfg.get("letter", "") == "X"
        stale_name   = cfg.get("name", "") == "OLDBOT"
        passed = not stale_letter and not stale_name
        checks.append({"name": "stale_config_overwritten", "passed": passed,
                        "detail": f"Old identity (X/OLDBOT) should be gone; letter='{cfg.get('letter')}' name='{cfg.get('name')}'"})
        if not passed:
            overall_passed = False
    except Exception as e:
        checks.append({"name": "stale_config_overwritten", "passed": False,
                        "detail": f"Exception: {e}"})
        overall_passed = False

    score = sum(1 for c in checks if c["passed"]) / len(checks)
    print(json.dumps({
        "passed": overall_passed,
        "score": round(score, 2),
        "checks": checks
    }))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "args", "passed": False,
                                      "detail": "No workspace path provided"}]}))
        sys.exit(1)
    run_checks(sys.argv[1])