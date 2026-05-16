import sys
import json
import os
from pathlib import Path

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def load_jsonl(path):
    entries = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries

def main(workspace):
    checks = []
    overall_passed = True

    CONFIG_PATH = os.path.join(workspace, "configs", "cae_config.json")
    STATE_PATH = os.path.join(workspace, ".sim_state.json")
    LOG_PATH = os.path.join(workspace, "skill_runner_invocations.jsonl")

    EXPECTED_APP = "abaqus"
    EXPECTED_PATH_FRAGMENT = "/workspace/solvers"  # agent must use a path under this or any custom path
    EXPECTED_FILE_FRAGMENT = "final_crash_model.inp"

    # --- CHECK 1: Config file was modified to include saved path for abaqus ---
    try:
        config = load_json(CONFIG_PATH)
        saved_paths = config.get("saved_paths", {})
        abaqus_saved = saved_paths.get("abaqus", "")
        check1_passed = bool(abaqus_saved and len(abaqus_saved) > 5)
        checks.append({
            "name": "abaqus_path_saved_in_config",
            "passed": check1_passed,
            "detail": f"saved_paths.abaqus = '{abaqus_saved}'" if check1_passed else f"No abaqus path found in saved_paths. Got: {saved_paths}"
        })
        if not check1_passed:
            overall_passed = False
    except Exception as e:
        checks.append({"name": "abaqus_path_saved_in_config", "passed": False, "detail": f"Exception: {e}"})
        overall_passed = False

    # --- CHECK 2: set_app_path skill was called with correct payload structure ---
    try:
        invocations = load_jsonl(LOG_PATH)
        set_path_calls = [
            inv for inv in invocations
            if inv.get("payload", {}).get("skill") == "set_app_path"
            and inv.get("payload", {}).get("args", {}).get("app") == "abaqus"
        ]
        check2_passed = len(set_path_calls) >= 1
        # Also check it used config_file pointing to our config
        if check2_passed:
            for call in set_path_calls:
                cfg = call["payload"]["args"].get("config_file", "")
                result_status = call.get("result", {}).get("status", "")
                detail = f"set_app_path called for abaqus. config_file='{cfg}', result_status='{result_status}'"
        else:
            detail = f"No set_app_path call found for abaqus in {len(invocations)} total invocations"
        checks.append({
            "name": "set_app_path_called_correctly",
            "passed": check2_passed,
            "detail": detail
        })
        if not check2_passed:
            overall_passed = False
    except Exception as e:
        checks.append({"name": "set_app_path_called_correctly", "passed": False, "detail": f"Exception: {e}"})
        overall_passed = False

    # --- CHECK 3: detect_app_path was called for abaqus and returned found=True ---
    try:
        invocations = load_jsonl(LOG_PATH)
        detect_calls = [
            inv for inv in invocations
            if inv.get("payload", {}).get("skill") == "detect_app_path"
            and inv.get("payload", {}).get("args", {}).get("app") == "abaqus"
        ]
        detect_success = any(
            inv.get("result", {}).get("found") == True
            for inv in detect_calls
        )
        check3_passed = len(detect_calls) >= 1 and detect_success
        detail = (
            f"detect_app_path called {len(detect_calls)} time(s), found=True: {detect_success}"
            if detect_calls else
            "detect_app_path was never called for abaqus"
        )
        checks.append({
            "name": "detect_app_path_called_and_found",
            "passed": check3_passed,
            "detail": detail
        })
        if not check3_passed:
            overall_passed = False
    except Exception as e:
        checks.append({"name": "detect_app_path_called_and_found", "passed": False, "detail": f"Exception: {e}"})
        overall_passed = False

    # --- CHECK 4: open_file_in_app was called with correct skill name, app, file_path containing final_crash_model.inp ---
    try:
        invocations = load_jsonl(LOG_PATH)
        open_calls = [
            inv for inv in invocations
            if inv.get("payload", {}).get("skill") == "open_file_in_app"
            and inv.get("payload", {}).get("args", {}).get("app") == "abaqus"
        ]
        open_with_correct_file = [
            inv for inv in open_calls
            if EXPECTED_FILE_FRAGMENT in inv.get("payload", {}).get("args", {}).get("file_path", "")
        ]
        check4_passed = len(open_with_correct_file) >= 1
        if check4_passed:
            sample = open_with_correct_file[0]["payload"]["args"]
            detail = f"open_file_in_app called with file_path='{sample.get('file_path')}', auto_launch={sample.get('auto_launch')}, wait_seconds={sample.get('wait_seconds')}"
        else:
            detail = f"open_file_in_app not called correctly. open_calls: {len(open_calls)}, with correct file: {len(open_with_correct_file)}"
        checks.append({
            "name": "open_file_in_app_called_correctly",
            "passed": check4_passed,
            "detail": detail
        })
        if not check4_passed:
            overall_passed = False
    except Exception as e:
        checks.append({"name": "open_file_in_app_called_correctly", "passed": False, "detail": f"Exception: {e}"})
        overall_passed = False

    # --- CHECK 5: auto_launch=true was used in open_file_in_app (required for non-running app) ---
    try:
        invocations = load_jsonl(LOG_PATH)
        open_calls = [
            inv for inv in invocations
            if inv.get("payload", {}).get("skill") == "open_file_in_app"
            and inv.get("payload", {}).get("args", {}).get("app") == "abaqus"
            and EXPECTED_FILE_FRAGMENT in inv.get("payload", {}).get("args", {}).get("file_path", "")
        ]
        auto_launch_used = any(
            inv.get("payload", {}).get("args", {}).get("auto_launch") == True
            for inv in open_calls
        )
        checks.append({
            "name": "auto_launch_enabled",
            "passed": auto_launch_used,
            "detail": f"auto_launch=True found in open_file_in_app call: {auto_launch_used}"
        })
        if not auto_launch_used:
            overall_passed = False
    except Exception as e:
        checks.append({"name": "auto_launch_enabled", "passed": False, "detail": f"Exception: {e}"})
        overall_passed = False

    # --- CHECK 6: State reflects abaqus running and file open ---
    try:
        state = load_json(STATE_PATH)
        running = state.get("running_apps", [])
        abaqus_running = "abaqus" in running
        open_files = state.get("open_files", {})
        abaqus_file = open_files.get("abaqus", "")
        file_correct = EXPECTED_FILE_FRAGMENT in abaqus_file
        check6_passed = abaqus_running and file_correct
        checks.append({
            "name": "final_state_abaqus_running_with_file",
            "passed": check6_passed,
            "detail": f"running_apps={running}, open_files.abaqus='{abaqus_file}'"
        })
        if not check6_passed:
            overall_passed = False
    except Exception as e:
        checks.append({"name": "final_state_abaqus_running_with_file", "passed": False, "detail": f"Exception: {e}"})
        overall_passed = False

    # --- CHECK 7: Skill names are exactly correct (proprietary trap: is_app_runing typo, get_activate_app) ---
    try:
        invocations = load_jsonl(LOG_PATH)
        skill_names_used = [inv.get("payload", {}).get("skill", "") for inv in invocations]
        # Check that agent did NOT use wrong spelling "is_app_running" (with double n)
        used_wrong_running = "is_app_running" in skill_names_used
        used_wrong_active = "get_active_app" in skill_names_used
        # Check if they used correct names if they used these skills at all
        used_correct_running = "is_app_runing" in skill_names_used
        used_correct_active = "get_activate_app" in skill_names_used
        # Only penalize if they used the wrong name AND not the right one
        # (they may not need to call these at all for this task)
        spelling_trap_passed = not used_wrong_running and not used_wrong_active
        detail = (
            f"Skills used: {list(set(skill_names_used))}. "
            f"Wrong 'is_app_running': {used_wrong_running}. "
            f"Wrong 'get_active_app': {used_wrong_active}. "
            f"Correct 'is_app_runing': {used_correct_running}. "
            f"Correct 'get_activate_app': {used_correct_active}."
        )
        checks.append({
            "name": "correct_skill_name_spelling",
            "passed": spelling_trap_passed,
            "detail": detail
        })
        if not spelling_trap_passed:
            overall_passed = False
    except Exception as e:
        checks.append({"name": "correct_skill_name_spelling", "passed": False, "detail": f"Exception: {e}"})
        overall_passed = False

    # --- CHECK 8: config_file argument pointed to the correct non-default config ---
    try:
        invocations = load_jsonl(LOG_PATH)
        # All calls that specify config_file should point to cae_config.json (not some other file)
        wrong_config_calls = [
            inv for inv in invocations
            if "config_file" in inv.get("payload", {}).get("args", {})
            and "cae_config.json" not in inv.get("payload", {}).get("args", {}).get("config_file", "")
        ]
        # Also check that at least set_app_path used the cae_config.json path
        set_path_with_correct_config = [
            inv for inv in invocations
            if inv.get("payload", {}).get("skill") == "set_app_path"
            and inv.get("payload", {}).get("args", {}).get("app") == "abaqus"
            and "cae_config.json" in inv.get("payload", {}).get("args", {}).get("config_file", "")
        ]
        # If config was updated correctly (check 1 passed), this is the key signal
        # We allow that the agent may omit config_file if default was changed, but primary check is config state
        config_check_passed = len(wrong_config_calls) == 0
        detail = (
            f"Wrong config_file references: {len(wrong_config_calls)}. "
            f"set_app_path calls with correct cae_config.json: {len(set_path_with_correct_config)}"
        )
        checks.append({
            "name": "correct_config_file_used",
            "passed": config_check_passed,
            "detail": detail
        })
        if not config_check_passed:
            overall_passed = False
    except Exception as e:
        checks.append({"name": "correct_config_file_used", "passed": False, "detail": f"Exception: {e}"})
        overall_passed = False

    # Compute score
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / len(checks), 4) if checks else 0.0

    output = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    main(workspace)