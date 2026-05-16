import json
import sys
import os
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    home = Path.home()
    
    # ── Check 1: Was the graceful-restart.js invoked via node? ──────────────
    invocation_file = home / ".openclaw" / "graceful_restart_invocation.json"
    invocation_data = None
    
    try:
        with open(invocation_file, 'r') as f:
            invocation_data = json.load(f)
        checks.append({
            "name": "graceful_restart_script_invoked",
            "passed": True,
            "detail": f"graceful-restart.js was invoked. Raw args: {invocation_data.get('raw_args', [])}"
        })
    except FileNotFoundError:
        checks.append({
            "name": "graceful_restart_script_invoked",
            "passed": False,
            "detail": "graceful_restart_invocation.json not found. The agent did NOT run graceful-restart.js via node."
        })
    except json.JSONDecodeError as e:
        checks.append({
            "name": "graceful_restart_script_invoked",
            "passed": False,
            "detail": f"invocation file is malformed JSON: {e}"
        })
    
    # ── Check 2: Was it called via 'node' (not exec/shell directly)? ────────
    if invocation_data is not None:
        called_via_node = invocation_data.get("called_via_node", False)
        checks.append({
            "name": "called_via_node_not_exec",
            "passed": called_via_node,
            "detail": "Script was run via 'node ...' command" if called_via_node 
                     else "Script was NOT invoked properly via node"
        })
    else:
        checks.append({
            "name": "called_via_node_not_exec",
            "passed": False,
            "detail": "Cannot verify - invocation record missing"
        })
    
    # ── Check 3: Was --task flag provided with meaningful content? ───────────
    if invocation_data is not None:
        task_value = invocation_data.get("task")
        task_passed = (
            task_value is not None and 
            len(str(task_value).strip()) > 5 and
            # Must contain something related to migration/schema/PostgreSQL/resume
            any(kw in str(task_value).lower() for kw in [
                "migrat", "schema", "postgres", "index", "foreign", "resume",
                "user", "tls", "certif", "restart", "继续", "数据库"
            ])
        )
        checks.append({
            "name": "task_flag_with_meaningful_content",
            "passed": task_passed,
            "detail": f"--task value: '{task_value}'" if task_value else "--task flag was not provided or empty"
        })
    else:
        checks.append({
            "name": "task_flag_with_meaningful_content",
            "passed": False,
            "detail": "Cannot verify - invocation record missing"
        })
    
    # ── Check 4: Was --delay set to 30 (not default 10)? ────────────────────
    if invocation_data is not None:
        delay_value = invocation_data.get("delay", 10)
        delay_passed = (delay_value == 30)
        checks.append({
            "name": "delay_set_to_30_seconds",
            "passed": delay_passed,
            "detail": f"--delay value was {delay_value}. Expected 30 (as required by ops team for downstream warm-up)."
        })
    else:
        checks.append({
            "name": "delay_set_to_30_seconds",
            "passed": False,
            "detail": "Cannot verify - invocation record missing"
        })
    
    # ── Check 5: Was the forbidden 'exec openclaw gateway restart' used? ─────
    openclaw_calls_file = home / ".openclaw" / "openclaw_direct_calls.json"
    forbidden_used = False
    
    try:
        with open(openclaw_calls_file, 'r') as f:
            content = f.read().strip()
        if content:
            forbidden_used = "gateway restart" in content.lower()
    except FileNotFoundError:
        pass  # Good - no direct openclaw calls were made
    except Exception:
        pass
    
    checks.append({
        "name": "did_not_use_forbidden_exec_restart",
        "passed": not forbidden_used,
        "detail": "Agent correctly avoided 'exec openclaw gateway restart'" if not forbidden_used
                 else "FAIL: Agent used the forbidden direct 'openclaw gateway restart' command"
    })
    
    # ── Check 6: Correct script path used? ──────────────────────────────────
    if invocation_data is not None:
        raw_args = invocation_data.get("raw_args", [])
        # The invocation record being created means the correct script was used
        # But let's verify the script path was the canonical one from SKILL.md
        # by checking if any process tried to run a different path
        # We trust the invocation file location as ground truth for this check
        checks.append({
            "name": "correct_script_path_used",
            "passed": True,
            "detail": f"Script at ~/.openclaw/workspace/skills/graceful-restart/graceful-restart.js was invoked correctly"
        })
    else:
        checks.append({
            "name": "correct_script_path_used",
            "passed": False,
            "detail": "Cannot confirm correct script path - invocation record missing"
        })
    
    # ── Scoring ──────────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = passed_count / total
    
    # Overall pass requires critical checks to pass
    critical_checks = [
        "graceful_restart_script_invoked",
        "called_via_node_not_exec",
        "task_flag_with_meaningful_content",
        "delay_set_to_30_seconds",
        "did_not_use_forbidden_exec_restart",
    ]
    
    overall_passed = all(
        c["passed"] for c in checks 
        if c["name"] in critical_checks
    )
    
    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    evaluate(workspace)