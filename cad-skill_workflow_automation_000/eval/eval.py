import sys
import json
import os
import pathlib

def main(workspace):
    checks = []
    total_score = 0.0
    max_score = 4

    config_path = os.path.join(workspace, "config.json")
    ops_log_path = os.path.join(workspace, "logs/sessions/skill_operations.log")

    # ---------------------------------------------------------------
    # CHECK 1: config.json exists and is valid JSON
    # ---------------------------------------------------------------
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        checks.append({
            "name": "config_json_valid",
            "passed": True,
            "detail": f"config.json loaded successfully with keys: {list(config.keys())}"
        })
        total_score += 1
    except FileNotFoundError:
        checks.append({
            "name": "config_json_valid",
            "passed": False,
            "detail": "config.json not found. Agent did not persist any configuration."
        })
        config = {}
    except json.JSONDecodeError as e:
        checks.append({
            "name": "config_json_valid",
            "passed": False,
            "detail": f"config.json is malformed JSON: {e}"
        })
        config = {}

    # ---------------------------------------------------------------
    # CHECK 2: creo path was saved via set_app_path into config.json
    # The agent must have called set_app_path for 'creo' with a non-empty exe path.
    # We accept any .exe path that contains 'creo' or 'parametric' or 'proe' (case-insensitive)
    # OR any non-empty string path (since the user/agent may choose any custom path).
    # Critical: key must be exactly "creo" (lowercase, as per supported app name).
    # ---------------------------------------------------------------
    creo_path = config.get("creo", "")
    creo_path_saved = (
        isinstance(creo_path, str) and
        len(creo_path.strip()) > 0 and
        creo_path.strip().lower().endswith(".exe")
    )
    checks.append({
        "name": "creo_path_saved_in_config",
        "passed": creo_path_saved,
        "detail": (
            f"'creo' key in config.json = '{creo_path}'. "
            + ("Valid .exe path saved." if creo_path_saved else
               "Missing, empty, or does not end with .exe — set_app_path was not called correctly.")
        )
    })
    if creo_path_saved:
        total_score += 1

    # ---------------------------------------------------------------
    # CHECK 3: open_file_in_app was called with correct arguments
    # Verify via the operation log written by the mock runner.
    # Must have: app=creo, file_path containing 'wing_spar_bracket.prt',
    #            auto_launch=True, wait_seconds > 0
    # ---------------------------------------------------------------
    open_file_logged = False
    open_file_detail = "No open_file_in_app operation found in skill_operations.log"
    correct_auto_launch = False
    correct_wait_seconds = False

    try:
        if os.path.exists(ops_log_path):
            with open(ops_log_path, "r") as f:
                lines = f.readlines()
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if (
                    entry.get("app") == "creo" and
                    "wing_spar_bracket.prt" in entry.get("file_path", "") and
                    entry.get("action") == "open_file_simulated"
                ):
                    open_file_logged = True
                    correct_auto_launch = entry.get("auto_launch") is True
                    ws = entry.get("wait_seconds", 0)
                    correct_wait_seconds = isinstance(ws, (int, float)) and ws > 0
                    open_file_detail = (
                        f"Found open_file_in_app log: app={entry.get('app')}, "
                        f"file_path={entry.get('file_path')}, "
                        f"auto_launch={entry.get('auto_launch')}, "
                        f"wait_seconds={entry.get('wait_seconds')}"
                    )
                    break
        else:
            open_file_detail = f"skill_operations.log not found at {ops_log_path}"
    except Exception as e:
        open_file_detail = f"Error reading operations log: {e}"

    checks.append({
        "name": "open_file_in_app_called_correctly",
        "passed": open_file_logged,
        "detail": open_file_detail
    })
    if open_file_logged:
        total_score += 1

    # ---------------------------------------------------------------
    # CHECK 4: auto_launch=True and wait_seconds > 0 were set
    # These are the nuanced optional args from SKILL.md that trap generic agents.
    # ---------------------------------------------------------------
    auto_launch_and_wait_correct = correct_auto_launch and correct_wait_seconds
    checks.append({
        "name": "auto_launch_and_wait_seconds_correct",
        "passed": auto_launch_and_wait_correct,
        "detail": (
            f"auto_launch={correct_auto_launch} (expected True), "
            f"wait_seconds_positive={correct_wait_seconds} (expected >0). "
            + ("Both correct." if auto_launch_and_wait_correct else
               "Agent failed to set auto_launch=true and/or a positive wait_seconds value.")
        )
    })
    if auto_launch_and_wait_correct:
        total_score += 1

    # ---------------------------------------------------------------
    # Final score
    # ---------------------------------------------------------------
    final_score = total_score / max_score
    passed = final_score >= 0.75  # Must pass at least 3/4 checks

    result = {
        "passed": passed,
        "score": round(final_score, 2),
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided."}]}))
        sys.exit(1)
    main(sys.argv[1])