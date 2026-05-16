import sys
import json
import os
from pathlib import Path

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def run_checks(workspace):
    ws = Path(workspace)
    checks = []
    
    # ── CHECK 1: openclaw.json has correct camelCase field names ──────────────
    try:
        config_path = ws / "openclaw.json"
        cfg = load_json(config_path)
        
        # Must have 'toolkitRoot' (camelCase), not 'toolkit_root'
        has_toolkit_root = "toolkitRoot" in cfg and isinstance(cfg["toolkitRoot"], str) and len(cfg["toolkitRoot"]) > 0
        no_snake_toolkit = "toolkit_root" not in cfg
        
        checks.append({
            "name": "openclaw.json has 'toolkitRoot' (camelCase, not snake_case)",
            "passed": has_toolkit_root and no_snake_toolkit,
            "detail": f"toolkitRoot present: {has_toolkit_root}, snake_case absent: {no_snake_toolkit}. Keys found: {list(cfg.keys())}"
        })
        
        # Must have 'defaultProjectPath' (not 'project_path')
        has_default_project = "defaultProjectPath" in cfg
        no_snake_project = "project_path" not in cfg
        checks.append({
            "name": "openclaw.json has 'defaultProjectPath' (not 'project_path')",
            "passed": has_default_project and no_snake_project,
            "detail": f"defaultProjectPath: {has_default_project}, project_path absent: {no_snake_project}"
        })
        
        # Must have 'executionMode' (not 'mode')
        has_execution_mode = "executionMode" in cfg
        no_bare_mode = "mode" not in cfg
        valid_mode_value = cfg.get("executionMode", "") in ("direct", "wsl")
        checks.append({
            "name": "openclaw.json has 'executionMode' with valid value ('direct' or 'wsl')",
            "passed": has_execution_mode and no_bare_mode and valid_mode_value,
            "detail": f"executionMode: {has_execution_mode}, value: {cfg.get('executionMode')}, bare 'mode' absent: {no_bare_mode}"
        })
        
        # Must have 'timeoutMs' as a number (not string 'timeout')
        has_timeout_ms = "timeoutMs" in cfg
        no_bare_timeout = "timeout" not in cfg
        timeout_is_number = isinstance(cfg.get("timeoutMs"), (int, float)) if has_timeout_ms else False
        checks.append({
            "name": "openclaw.json has 'timeoutMs' as a number (not string 'timeout')",
            "passed": has_timeout_ms and no_bare_timeout and timeout_is_number,
            "detail": f"timeoutMs: {has_timeout_ms}, value type: {type(cfg.get('timeoutMs')).__name__}, is_number: {timeout_is_number}"
        })
        
        # toolkitRoot must point to the cursor-agent-system directory
        toolkit_root_val = cfg.get("toolkitRoot", "")
        # It should contain 'cursor-agent-system' in the path
        toolkit_root_valid = "cursor-agent-system" in toolkit_root_val
        checks.append({
            "name": "toolkitRoot points to the cursor-agent-system directory",
            "passed": toolkit_root_valid,
            "detail": f"toolkitRoot value: '{toolkit_root_val}'"
        })
        
    except Exception as e:
        checks.append({
            "name": "openclaw.json readable and parseable",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ── CHECK 2: Runtime directories created under toolkitRoot ───────────────
    try:
        config_path = ws / "openclaw.json"
        cfg = load_json(config_path)
        toolkit_root = cfg.get("toolkitRoot", "")
        
        if not toolkit_root:
            # Fallback: look for cursor-agent-system
            toolkit_root = str(ws / "cursor-agent-system")
        
        for dirname in ["status", "tasks", "logs"]:
            dir_path = Path(toolkit_root) / dirname
            exists = dir_path.exists() and dir_path.is_dir()
            checks.append({
                "name": f"Runtime directory '{dirname}/' exists under toolkitRoot",
                "passed": exists,
                "detail": f"Expected: {dir_path}, exists: {exists}"
            })
    except Exception as e:
        for dirname in ["status", "tasks", "logs"]:
            checks.append({
                "name": f"Runtime directory '{dirname}/' exists under toolkitRoot",
                "passed": False,
                "detail": f"Exception reading config: {e}"
            })

    # ── CHECK 3: spawn_call.json — exact args array for spawn-cursor.sh ──────
    try:
        # Find spawn_call.json anywhere in workspace
        matches = list(ws.rglob("spawn_call.json"))
        if not matches:
            checks.append({
                "name": "spawn_call.json exists",
                "passed": False,
                "detail": "File not found anywhere in workspace"
            })
            # Add placeholder failures for sub-checks
            for sub in ["spawn args: taskName first", "spawn args: taskDescription second",
                        "spawn args: projectPath third", "spawn args: --json present",
                        "spawn args: --priority high present", "spawn args: --eta 30min present",
                        "spawn args: correct ordering (--json before --priority)"]:
                checks.append({"name": sub, "passed": False, "detail": "spawn_call.json not found"})
        else:
            spawn_data = load_json(matches[0])
            checks.append({
                "name": "spawn_call.json exists",
                "passed": True,
                "detail": f"Found at {matches[0]}"
            })
            
            # The args should be a list
            args = spawn_data if isinstance(spawn_data, list) else spawn_data.get("args", spawn_data.get("arguments", []))
            
            # Per handleSpawnTool: args = [taskName, taskDescription, projectPath, "--json"]
            # then optionally: ["--priority", "high", "--eta", "30min"]
            # Expected: ["refactor-auth", "Refactor the JWT...", "/workspace/fintech-api", "--json", "--priority", "high", "--eta", "30min"]
            
            arg_strs = [str(a) for a in args]
            
            has_task_name_first = len(arg_strs) > 0 and arg_strs[0] == "refactor-auth"
            checks.append({
                "name": "spawn args: taskName is first element ('refactor-auth')",
                "passed": has_task_name_first,
                "detail": f"First element: {arg_strs[0] if arg_strs else 'EMPTY'}"
            })
            
            has_desc_second = len(arg_strs) > 1 and "RS256" in arg_strs[1] and "HS256" in arg_strs[1]
            checks.append({
                "name": "spawn args: taskDescription is second element (contains RS256 and HS256)",
                "passed": has_desc_second,
                "detail": f"Second element: {arg_strs[1] if len(arg_strs) > 1 else 'MISSING'}"
            })
            
            has_project_third = len(arg_strs) > 2 and "fintech-api" in arg_strs[2]
            checks.append({
                "name": "spawn args: projectPath is third element (contains 'fintech-api')",
                "passed": has_project_third,
                "detail": f"Third element: {arg_strs[2] if len(arg_strs) > 2 else 'MISSING'}"
            })
            
            has_json_flag = "--json" in arg_strs
            json_idx = arg_strs.index("--json") if has_json_flag else -1
            checks.append({
                "name": "spawn args: '--json' flag is present",
                "passed": has_json_flag,
                "detail": f"--json at index: {json_idx}"
            })
            
            has_priority = "--priority" in arg_strs
            priority_val_ok = False
            if has_priority:
                pi = arg_strs.index("--priority")
                priority_val_ok = pi + 1 < len(arg_strs) and arg_strs[pi + 1] == "high"
            checks.append({
                "name": "spawn args: '--priority high' pair present",
                "passed": has_priority and priority_val_ok,
                "detail": f"--priority found: {has_priority}, value 'high': {priority_val_ok}"
            })
            
            has_eta = "--eta" in arg_strs
            eta_val_ok = False
            if has_eta:
                ei = arg_strs.index("--eta")
                eta_val_ok = ei + 1 < len(arg_strs) and arg_strs[ei + 1] == "30min"
            checks.append({
                "name": "spawn args: '--eta 30min' pair present",
                "passed": has_eta and eta_val_ok,
                "detail": f"--eta found: {has_eta}, value '30min': {eta_val_ok}"
            })
            
            # Critical order check: --json must come at index 3 (right after projectPath)
            json_at_index_3 = json_idx == 3
            checks.append({
                "name": "spawn args: '--json' appears at index 3 (immediately after projectPath)",
                "passed": json_at_index_3,
                "detail": f"--json index: {json_idx}, expected: 3"
            })
            
    except Exception as e:
        checks.append({
            "name": "spawn_call.json parseable",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ── CHECK 4: kill_call.json — exact args array for kill-session.sh ───────
    try:
        matches = list(ws.rglob("kill_call.json"))
        if not matches:
            checks.append({
                "name": "kill_call.json exists",
                "passed": False,
                "detail": "File not found anywhere in workspace"
            })
            for sub in ["kill args: sessionQuery first", "kill args: --yes present (always injected)",
                        "kill args: --json present", "kill args: --force present",
                        "kill args: --purge present", "kill args: --yes before optional flags"]:
                checks.append({"name": sub, "passed": False, "detail": "kill_call.json not found"})
        else:
            kill_data = load_json(matches[0])
            checks.append({
                "name": "kill_call.json exists",
                "passed": True,
                "detail": f"Found at {matches[0]}"
            })
            
            args = kill_data if isinstance(kill_data, list) else kill_data.get("args", kill_data.get("arguments", []))
            arg_strs = [str(a) for a in args]
            
            # Per handleKillTool: args = [sessionQuery, "--yes", "--json"] then optional --force --purge
            has_session_first = len(arg_strs) > 0 and arg_strs[0] == "cursor-refactor-auth-001"
            checks.append({
                "name": "kill args: sessionQuery is first element ('cursor-refactor-auth-001')",
                "passed": has_session_first,
                "detail": f"First element: {arg_strs[0] if arg_strs else 'EMPTY'}"
            })
            
            # PROPRIETARY TRAP: --yes is ALWAYS injected (hardcoded in handleKillTool), not optional
            has_yes = "--yes" in arg_strs
            yes_idx = arg_strs.index("--yes") if has_yes else -1
            checks.append({
                "name": "kill args: '--yes' present (always injected, proprietary behavior)",
                "passed": has_yes,
                "detail": f"--yes found at index: {yes_idx}. This is hardcoded in handleKillTool regardless of params."
            })
            
            has_json = "--json" in arg_strs
            checks.append({
                "name": "kill args: '--json' flag present",
                "passed": has_json,
                "detail": f"--json found: {has_json}"
            })
            
            has_force = "--force" in arg_strs
            checks.append({
                "name": "kill args: '--force' flag present (force=true in kill_inputs)",
                "passed": has_force,
                "detail": f"--force found: {has_force}"
            })
            
            has_purge = "--purge" in arg_strs
            checks.append({
                "name": "kill args: '--purge' flag present (purge=true in kill_inputs)",
                "passed": has_purge,
                "detail": f"--purge found: {has_purge}"
            })
            
            # --yes must appear before --force and --purge (index 1)
            yes_at_1 = yes_idx == 1
            checks.append({
                "name": "kill args: '--yes' appears at index 1 (right after sessionQuery)",
                "passed": yes_at_1,
                "detail": f"--yes index: {yes_idx}, expected: 1"
            })
            
    except Exception as e:
        checks.append({
            "name": "kill_call.json parseable",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    return checks

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    checks = run_checks(workspace)
    
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = passed_count / total if total > 0 else 0.0
    all_passed = passed_count == total
    
    result = {
        "passed": all_passed,
        "score": round(score, 4),
        "checks": checks
    }
    
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()