#!/bin/bash
set -e

# Install the mock skill_runner.py into the workspace root
cat > /workspace/skill_runner.py << 'PYTHON_EOF'
#!/usr/bin/env python3
"""
Mock skill_runner.py for CAE Skill evaluation.
Simulates the real skill runner behavior for: set_app_path, detect_app_path,
open_file_in_app, is_app_runing, get_running_apps, get_activate_app.
Stores state in the config_file specified or defaults to config.json.
Logs all invocations to /workspace/skill_runner_invocations.jsonl
"""
import sys
import json
import os
from pathlib import Path

DEFAULT_CONFIG = "/workspace/configs/cae_config.json"
LOG_FILE = "/workspace/skill_runner_invocations.jsonl"
STATE_FILE = "/workspace/.sim_state.json"

SUPPORTED_APPS = ["abaqus", "ansys", "ansa", "hyperworks"]


def load_config(config_file):
    with open(config_file, "r") as f:
        return json.load(f)


def save_config(config_file, config):
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"running_apps": [], "active_app": None, "open_files": {}}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def log_invocation(payload, result):
    entry = {"payload": payload, "result": result}
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def handle(payload):
    skill = payload.get("skill")
    args = payload.get("args", {})
    config_file = args.get("config_file", DEFAULT_CONFIG)

    if skill == "set_app_path":
        app = args.get("app")
        path = args.get("path")
        if app not in SUPPORTED_APPS:
            return {"status": "error", "message": f"Unsupported app: {app}"}
        if not app or not path:
            return {"status": "error", "message": "app and path are required"}
        config = load_config(config_file)
        if "saved_paths" not in config:
            config["saved_paths"] = {}
        config["saved_paths"][app] = path
        save_config(config_file, config)
        return {"status": "success", "message": f"Path for {app} saved: {path}"}

    elif skill == "detect_app_path":
        app = args.get("app")
        if app not in SUPPORTED_APPS:
            return {"status": "error", "message": f"Unsupported app: {app}"}
        config = load_config(config_file)
        saved = config.get("saved_paths", {}).get(app)
        if saved:
            return {"status": "success", "found": True, "path": saved, "source": "saved_paths"}
        common = config.get("common_install_paths", {}).get(app, [])
        for p in common:
            if os.path.exists(p):
                return {"status": "success", "found": True, "path": p, "source": "common_install_paths"}
        return {"status": "success", "found": False, "message": f"Executable for {app} not found. Please provide the full path."}

    elif skill == "open_file_in_app":
        app = args.get("app")
        file_path = args.get("file_path")
        auto_launch = args.get("auto_launch", False)
        wait_seconds = args.get("wait_seconds", 0)
        if app not in SUPPORTED_APPS:
            return {"status": "error", "message": f"Unsupported app: {app}"}
        if not file_path:
            return {"status": "error", "message": "file_path is required"}
        # Check app path
        config = load_config(config_file)
        saved = config.get("saved_paths", {}).get(app)
        state = load_state()
        if not saved and app not in state.get("running_apps", []):
            return {"status": "error", "message": f"Cannot open file: {app} path not set and app not running. Set path first or launch manually."}
        # Simulate opening
        state["running_apps"] = list(set(state.get("running_apps", []) + [app]))
        state["active_app"] = app
        state["open_files"][app] = file_path
        save_state(state)
        return {
            "status": "success",
            "message": f"Opened {file_path} in {app}",
            "auto_launch": auto_launch,
            "wait_seconds": wait_seconds,
            "app_path": saved
        }

    elif skill == "is_app_runing":  # intentional typo per SKILL.md
        app = args.get("app")
        if app not in SUPPORTED_APPS:
            return {"status": "error", "message": f"Unsupported app: {app}"}
        state = load_state()
        running = app in state.get("running_apps", [])
        return {"status": "success", "app": app, "is_running": running}

    elif skill == "close_app":
        app = args.get("app")
        force = args.get("force", False)
        if app not in SUPPORTED_APPS:
            return {"status": "error", "message": f"Unsupported app: {app}"}
        state = load_state()
        if app in state.get("running_apps", []):
            state["running_apps"].remove(app)
        if state.get("active_app") == app:
            state["active_app"] = state["running_apps"][0] if state["running_apps"] else None
        if app in state.get("open_files", {}):
            del state["open_files"][app]
        save_state(state)
        return {"status": "success", "message": f"{app} closed (force={force})"}

    elif skill == "get_activate_app":  # intentional spelling per SKILL.md
        state = load_state()
        return {"status": "success", "active_app": state.get("active_app")}

    elif skill == "get_running_apps":
        state = load_state()
        return {"status": "success", "running_apps": state.get("running_apps", [])}

    elif skill == "launch_app":
        app = args.get("app")
        if app not in SUPPORTED_APPS:
            return {"status": "error", "message": f"Unsupported app: {app}"}
        config = load_config(config_file)
        saved = config.get("saved_paths", {}).get(app)
        if not saved:
            return {"status": "error", "message": f"No path found for {app}. Use set_app_path first."}
        state = load_state()
        state["running_apps"] = list(set(state.get("running_apps", []) + [app]))
        state["active_app"] = app
        save_state(state)
        return {"status": "success", "message": f"Launched {app} from {saved}"}

    else:
        return {"status": "error", "message": f"Unknown skill: {skill}"}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "Usage: python skill_runner.py '<json_payload>'"}))
        sys.exit(1)

    raw = sys.argv[1]
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        result = {"status": "error", "message": f"Invalid JSON: {e}"}
        print(json.dumps(result))
        sys.exit(1)

    result = handle(payload)
    log_invocation(payload, result)
    print(json.dumps(result))
PYTHON_EOF

chmod +x /workspace/skill_runner.py

# Initialize the state file and invocations log
echo '{"running_apps": [], "active_app": null, "open_files": {}}' > /workspace/.sim_state.json
touch /workspace/skill_runner_invocations.jsonl

echo "Setup complete. skill_runner.py is ready."