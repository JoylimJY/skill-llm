import sys
import json
import os
from pathlib import Path

def load_json_safe(path):
    try:
        with open(path, 'r') as f:
            return json.load(f), None
    except FileNotFoundError:
        return None, f"File not found: {path}"
    except json.JSONDecodeError as e:
        return None, f"JSON parse error in {path}: {e}"

def run_workflow_and_get_log(workspace):
    """Execute the agent's workflow script and return the call log."""
    import subprocess
    
    # Find the agent's output script
    candidates = list(Path(workspace).rglob("transmission_workflow.js"))
    if not candidates:
        return None, None, "transmission_workflow.js not found in workspace"
    
    script_path = candidates[0]
    
    # Reset the call log before running
    log_path = "/tmp/declaw_calls.json"
    with open(log_path, 'w') as f:
        json.dump([], f)
    
    try:
        result = subprocess.run(
            ["node", str(script_path)],
            capture_output=True, text=True, timeout=30,
            cwd=workspace,
            env={**os.environ, "DECLAW_LOG": log_path, "NODE_PATH": str(Path(workspace) / "node_modules")}
        )
    except subprocess.TimeoutExpired:
        return None, None, "Script timed out after 30s"
    except Exception as e:
        return None, None, f"Execution error: {e}"
    
    log, err = load_json_safe(log_path)
    return log, result, err

def evaluate(workspace):
    checks = []
    
    # Step 1: Find and execute the workflow script
    log, exec_result, err = run_workflow_and_get_log(workspace)
    
    script_exists = log is not None
    checks.append({
        "name": "transmission_workflow.js exists and executes",
        "passed": script_exists,
        "detail": err if err else f"Script executed, produced {len(log)} tool calls"
    })
    
    if not script_exists:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }
    
    TARGET_ADDR = "200:b33f:cafe:dead::7"
    TARGET_ALIAS = "NordsternPrimary"
    TARGET_PORT = 9055
    TARGET_MESSAGE = "Requesting access to dataset DS-2024-ARCTIC-07. Authorization code: NRSI-88421."
    
    tool_names = [call["tool"] for call in log]
    
    # ---- CHECK 2: p2p_add_peer called with correct address ----
    add_peer_calls = [c for c in log if c["tool"] == "p2p_add_peer"]
    correct_add_peer = any(
        c["params"].get("ygg_addr") == TARGET_ADDR
        for c in add_peer_calls
    )
    checks.append({
        "name": "p2p_add_peer called with correct target address",
        "passed": correct_add_peer,
        "detail": f"Found p2p_add_peer calls: {[c['params'] for c in add_peer_calls]}"
    })
    
    # ---- CHECK 3: p2p_add_peer with alias ----
    alias_set = any(
        c["params"].get("ygg_addr") == TARGET_ADDR and c["params"].get("alias") == TARGET_ALIAS
        for c in add_peer_calls
    )
    checks.append({
        "name": "p2p_add_peer includes alias 'NordsternPrimary'",
        "passed": alias_set,
        "detail": f"Alias check on add_peer calls: {[c['params'] for c in add_peer_calls]}"
    })
    
    # ---- CHECK 4: TOFU - p2p_add_peer must come BEFORE first p2p_send_message ----
    send_calls = [c for c in log if c["tool"] == "p2p_send_message"]
    if not add_peer_calls or not send_calls:
        tofu_order_ok = False
        tofu_detail = f"Missing calls: add_peer={len(add_peer_calls)}, send={len(send_calls)}"
    else:
        first_add_seq = min(c["seq"] for c in add_peer_calls if c["params"].get("ygg_addr") == TARGET_ADDR)
        first_send_seq = min(c["seq"] for c in send_calls)
        tofu_order_ok = first_add_seq < first_send_seq
        tofu_detail = f"First add_peer seq={first_add_seq}, first send seq={first_send_seq}"
    
    checks.append({
        "name": "TOFU: p2p_add_peer called BEFORE p2p_send_message (proprietary rule)",
        "passed": tofu_order_ok,
        "detail": tofu_detail
    })
    
    # ---- CHECK 5: p2p_send_message with correct address ----
    correct_send_addr = any(
        c["params"].get("ygg_addr") == TARGET_ADDR
        for c in send_calls
    )
    checks.append({
        "name": "p2p_send_message called with correct target address",
        "passed": correct_send_addr,
        "detail": f"Send calls: {[c['params'] for c in send_calls]}"
    })
    
    # ---- CHECK 6: p2p_send_message with non-default port 9055 (proprietary trap) ----
    correct_port = any(
        c["params"].get("ygg_addr") == TARGET_ADDR and c["params"].get("port") == TARGET_PORT
        for c in send_calls
    )
    checks.append({
        "name": "p2p_send_message uses explicit non-default port 9055 (not 8099)",
        "passed": correct_port,
        "detail": f"Send call ports: {[c['params'].get('port') for c in send_calls]}"
    })
    
    # ---- CHECK 7: Message content correct ----
    correct_msg = any(
        c["params"].get("message") == TARGET_MESSAGE
        for c in send_calls
    )
    checks.append({
        "name": "p2p_send_message contains exact required message text",
        "passed": correct_msg,
        "detail": f"Messages sent: {[c['params'].get('message', '')[:60] for c in send_calls]}"
    })
    
    # ---- CHECK 8: After failure, yggdrasil_check called before re-send ----
    # The mock makes the first send fail. The agent must call yggdrasil_check() after failure.
    # Check: yggdrasil_check appears in the log, and it appears after the first send and before any successful re-send
    ygg_check_calls = [c for c in log if c["tool"] == "yggdrasil_check"]
    
    if not ygg_check_calls or not send_calls:
        ygg_check_ok = False
        ygg_detail = f"yggdrasil_check calls: {len(ygg_check_calls)}, send calls: {len(send_calls)}"
    else:
        # First send should have failed (result.success=False), then yggdrasil_check, then retry
        first_send = send_calls[0]
        first_send_failed = first_send.get("result", {}).get("success") == False
        
        if first_send_failed:
            # yggdrasil_check must come after the failed send
            ygg_after_fail = any(c["seq"] > first_send["seq"] for c in ygg_check_calls)
            ygg_check_ok = ygg_after_fail
            ygg_detail = f"First send seq={first_send['seq']} (failed={first_send_failed}), yggdrasil_check seqs={[c['seq'] for c in ygg_check_calls]}"
        else:
            # If mock didn't trigger failure (script may have pre-emptively checked), 
            # still require yggdrasil_check to be present in workflow
            ygg_check_ok = len(ygg_check_calls) > 0
            ygg_detail = f"First send did not fail (seq={first_send['seq']}), but yggdrasil_check present: {len(ygg_check_calls) > 0}"
    
    checks.append({
        "name": "yggdrasil_check called after send failure (error handling rule)",
        "passed": ygg_check_ok,
        "detail": ygg_detail
    })
    
    # ---- CHECK 9: Successful delivery achieved ----
    successful_send = any(
        c["params"].get("ygg_addr") == TARGET_ADDR and 
        c.get("result", {}).get("success") == True
        for c in send_calls
    )
    checks.append({
        "name": "Message successfully delivered (second send after yggdrasil_check succeeds)",
        "passed": successful_send,
        "detail": f"Successful sends to target: {[c.get('result',{}) for c in send_calls if c['params'].get('ygg_addr')==TARGET_ADDR]}"
    })
    
    # Calculate score
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = passed_count / total
    
    # Hard requirements: TOFU order, correct port, yggdrasil_check after failure are mandatory
    hard_checks = ["TOFU: p2p_add_peer called BEFORE p2p_send_message (proprietary rule)",
                   "p2p_send_message uses explicit non-default port 9055 (not 8099)",
                   "yggdrasil_check called after send failure (error handling rule)"]
    
    hard_passed = all(c["passed"] for c in checks if c["name"] in hard_checks)
    overall_passed = hard_passed and score >= 0.75
    
    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))