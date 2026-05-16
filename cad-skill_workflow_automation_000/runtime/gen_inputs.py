import os
import json
import random
import pathlib

random.seed(42)

WORKSPACE = "/workspace"

# --- Create realistic deeply nested distractor directory structure ---
dirs = [
    "projects/aerospace/wing_assembly/revision_3/exports",
    "projects/aerospace/wing_assembly/revision_2/backups",
    "projects/aerospace/fuselage/cad_models/native",
    "projects/aerospace/fuselage/cad_models/step_exports",
    "projects/landing_gear/actuator/simulations",
    "projects/landing_gear/actuator/drawings",
    "tools/converters/step_iges",
    "tools/validators",
    "configs/legacy",
    "configs/archive",
    "logs/sessions",
    "logs/errors",
    "installers/creo_backup",
    "installers/solidworks_trial",
]

for d in dirs:
    pathlib.Path(os.path.join(WORKSPACE, d)).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
distractor_files = [
    ("projects/aerospace/wing_assembly/revision_3/exports/wing_v3.STEP", "STEP export placeholder"),
    ("projects/aerospace/wing_assembly/revision_3/exports/wing_v3.iges", "IGES export placeholder"),
    ("projects/aerospace/wing_assembly/revision_2/backups/wing_v2_backup.prt", "Creo part backup"),
    ("projects/aerospace/fuselage/cad_models/native/fuselage_main.prt", "Creo part file"),
    ("projects/aerospace/fuselage/cad_models/step_exports/fuselage_main.STEP", "STEP export"),
    ("projects/landing_gear/actuator/simulations/actuator_fea.sim", "FEA simulation data"),
    ("projects/landing_gear/actuator/drawings/actuator_drawing.pdf", "PDF drawing"),
    ("tools/converters/step_iges/convert.py", "# placeholder converter script\n"),
    ("tools/validators/validate_step.py", "# placeholder validator\n"),
    ("logs/sessions/session_2024_01_15.log", "Session started\nApplication launched\nSession ended\n"),
    ("logs/errors/error_2024_01_10.log", "ERROR: File not found\nERROR: Connection timeout\n"),
    ("installers/creo_backup/install_notes.txt", "Creo 8.0 backup installer notes. Path: C:\\PTC\\Creo 8.0.0.0\\Parametric\\bin\\parametric.exe"),
    ("installers/solidworks_trial/sw_trial_info.txt", "SolidWorks 2023 trial. Expired 2023-12-01."),
    ("configs/legacy/old_config.json", json.dumps({"solidworks": "C:\\SW2020\\sldworks.exe"}, indent=2)),
    ("configs/archive/config_backup_2023.json", json.dumps({"catia": "C:\\Dassault\\CATIA\\bin\\CNEXT.exe"}, indent=2)),
]

for rel_path, content in distractor_files:
    full_path = os.path.join(WORKSPACE, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# --- The target PRT file the agent must open ---
target_prt_dir = os.path.join(WORKSPACE, "projects/aerospace/wing_assembly/revision_3")
target_prt_path = os.path.join(target_prt_dir, "wing_spar_bracket.prt")
with open(target_prt_path, "w") as f:
    f.write("Creo Parametric Part File - wing_spar_bracket revision 3\n")

# --- Create skill_runner.py mock (simulates the real skill runner behavior) ---
# This mock handles: detect_app_path, set_app_path, open_file_in_app, is_app_runing
# It writes to config.json as the real runner would, and returns realistic JSON responses.
skill_runner_content = r'''#!/usr/bin/env python3
"""
Mock skill_runner.py - simulates CAD skill runner for testing.
Handles: detect_app_path, set_app_path, open_file_in_app, is_app_runing, 
         launch_app, close_app, get_running_apps, get_activate_app
"""
import sys
import json
import os
import pathlib

DEFAULT_CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

PREDEFINED_PATHS = {
    "solidworks": [
        "C:\\Program Files\\SOLIDWORKS Corp\\SOLIDWORKS\\SLDWORKS.exe",
        "C:\\Program Files (x86)\\SOLIDWORKS Corp\\SOLIDWORKS\\SLDWORKS.exe",
    ],
    "catia": [
        "C:\\Program Files\\Dassault Systemes\\B34\\win_b64\\code\\bin\\CNEXT.exe",
    ],
    "creo": [
        # Intentionally empty predefined paths for creo to force set_app_path workflow
    ],
    "ug": [
        "C:\\Siemens\\NX2212\\NXBIN\\ugraf.exe",
    ],
}

def load_config(config_file):
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_config(config_file, data):
    pathlib.Path(os.path.dirname(os.path.abspath(config_file))).mkdir(parents=True, exist_ok=True)
    with open(config_file, "w") as f:
        json.dump(data, f, indent=2)

def detect_app_path(app, config_file):
    config = load_config(config_file)
    # Check saved paths first
    if app in config and config[app]:
        return {"status": "found", "path": config[app], "source": "config"}
    # Check predefined paths (mock: none exist on this Linux system, so all predefined fail)
    predefined = PREDEFINED_PATHS.get(app, [])
    for p in predefined:
        if os.path.exists(p):
            return {"status": "found", "path": p, "source": "predefined"}
    return {"status": "not_found", "app": app, "message": f"Executable for '{app}' not found in predefined paths or config. Please provide the full executable path."}

def set_app_path(app, path, config_file):
    config = load_config(config_file)
    config[app] = path
    save_config(config_file, config)
    return {"status": "saved", "app": app, "path": path, "config_file": config_file}

def open_file_in_app(app, file_path, config_file, auto_launch=False, wait_seconds=0):
    detect_result = detect_app_path(app, config_file)
    if detect_result["status"] == "not_found":
        return {"status": "error", "message": detect_result["message"]}
    exe_path = detect_result["path"]
    # Mock: just record the open attempt
    result = {
        "status": "success",
        "app": app,
        "exe_path": exe_path,
        "file_path": file_path,
        "auto_launch": auto_launch,
        "wait_seconds": wait_seconds,
        "action": "open_file_simulated"
    }
    # Write an operation log to workspace
    log_path = os.path.join(os.path.dirname(config_file), "logs/sessions/skill_operations.log")
    pathlib.Path(os.path.dirname(log_path)).mkdir(parents=True, exist_ok=True)
    with open(log_path, "a") as lf:
        lf.write(json.dumps(result) + "\n")
    return result

def is_app_runing(app, config_file):
    # On this mock system, no CAD apps are running
    return {"status": "not_running", "app": app, "running": False}

def launch_app(app, config_file):
    detect_result = detect_app_path(app, config_file)
    if detect_result["status"] == "not_found":
        return {"status": "error", "message": detect_result["message"]}
    return {"status": "launched_simulated", "app": app, "exe_path": detect_result["path"]}

def close_app(app, config_file, force=False):
    return {"status": "closed_simulated", "app": app, "force": force}

def get_running_apps(config_file):
    return {"status": "success", "running_apps": []}

def get_activate_app(config_file):
    return {"status": "success", "active_app": None}

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "No input provided. Pass JSON payload as argument or pipe to stdin."}))
        sys.exit(1)
    
    # Accept payload as first argument or stdin
    if sys.argv[1] == "-":
        raw = sys.stdin.read()
    else:
        raw = sys.argv[1]
    
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        print(json.dumps({"status": "error", "message": f"Invalid JSON: {e}"}))
        sys.exit(1)
    
    skill = payload.get("skill")
    args = payload.get("args", {})
    config_file = args.get("config_file", DEFAULT_CONFIG)
    
    dispatch = {
        "detect_app_path": lambda: detect_app_path(args["app"], config_file),
        "set_app_path": lambda: set_app_path(args["app"], args["path"], config_file),
        "open_file_in_app": lambda: open_file_in_app(
            args["app"], args["file_path"], config_file,
            auto_launch=args.get("auto_launch", False),
            wait_seconds=args.get("wait_seconds", 0)
        ),
        "is_app_runing": lambda: is_app_runing(args["app"], config_file),
        "launch_app": lambda: launch_app(args["app"], config_file),
        "close_app": lambda: close_app(args["app"], config_file, force=args.get("force", False)),
        "get_running_apps": lambda: get_running_apps(config_file),
        "get_activate_app": lambda: get_activate_app(config_file),
    }
    
    if skill not in dispatch:
        print(json.dumps({"status": "error", "message": f"Unknown skill: {skill}"}))
        sys.exit(1)
    
    try:
        result = dispatch[skill]()
        print(json.dumps(result, indent=2))
    except KeyError as e:
        print(json.dumps({"status": "error", "message": f"Missing required argument: {e}"}))
        sys.exit(1)

if __name__ == "__main__":
    main()
'''

skill_runner_path = os.path.join(WORKSPACE, "skill_runner.py")
with open(skill_runner_path, "w") as f:
    f.write(skill_runner_content)

# --- Create a BROKEN/EMPTY config.json (no creo entry) ---
# This forces the agent to use detect_app_path -> not_found -> set_app_path workflow
config_path = os.path.join(WORKSPACE, "config.json")
initial_config = {
    "solidworks": "C:\\Program Files\\SOLIDWORKS Corp\\SOLIDWORKS\\SLDWORKS.exe"
}
with open(config_path, "w") as f:
    json.dump(initial_config, f, indent=2)

print("Workspace generated successfully.")
print(f"Target file: {target_prt_path}")
print(f"Config: {config_path}")
print(f"skill_runner.py: {skill_runner_path}")