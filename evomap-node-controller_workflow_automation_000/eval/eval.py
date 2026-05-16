import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    workspace = Path(workspace_dir)

    # --- Find node_ops.sh ---
    candidates = list(workspace.rglob("node_ops.sh"))
    if not candidates:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": "node_ops.sh not found anywhere in workspace"}]
        }

    script_path = candidates[0]
    checks.append({"name": "file_exists", "passed": True, "detail": f"Found at {script_path}"})

    try:
        content = script_path.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks + [{"name": "file_readable", "passed": False, "detail": str(e)}]
        }

    checks.append({"name": "file_readable", "passed": True, "detail": "Script content read successfully"})

    # ---- Values from cluster_config.ini ----
    CENTRAL_IP = "203.0.113.45"
    TOKYO_IP = "198.51.100.72"
    CENTRAL_NODE_ID = "evo-shenhai-prod-7f3a9c"
    TOKYO_NODE_ID = "evo-tela-tokyo-2b8d14"
    CENTRAL_SSH_KEY = "~/.ssh/id_ed25519_central"
    TOKYO_SSH_KEY = "~/.ssh/id_ed25519_tokyo"
    CENTRAL_NODE_PATH = "~/.nvm/versions/node/v22.22.0/bin/node"
    HUB_URL = "https://evomap.ai"

    # ---- CHECK 1: Environment variables are set ----
    # Must set CENTRAL_IP, TOKYO_IP, CENTRAL_SSH_KEY, TOKYO_SSH_KEY, NODE_PATH
    env_vars_required = {
        "CENTRAL_IP": CENTRAL_IP,
        "TOKYO_IP": TOKYO_IP,
        "CENTRAL_SSH_KEY": CENTRAL_SSH_KEY,
        "TOKYO_SSH_KEY": TOKYO_SSH_KEY,
        "NODE_PATH": CENTRAL_NODE_PATH,
    }
    env_check_passed = True
    env_details = []
    for var, val in env_vars_required.items():
        # Check that variable is exported/assigned with the correct value
        pattern = re.compile(
            rf'(?:export\s+)?{re.escape(var)}\s*=\s*["\']?{re.escape(val)}["\']?'
        )
        if pattern.search(content):
            env_details.append(f"{var}={val} ✓")
        else:
            env_check_passed = False
            env_details.append(f"{var}={val} ✗ (not found or wrong value)")
    checks.append({
        "name": "env_vars_correctly_set",
        "passed": env_check_passed,
        "detail": "; ".join(env_details)
    })

    # ---- CHECK 2: 深海 node start command ----
    # Must use: ssh -i $CENTRAL_SSH_KEY root@$CENTRAL_IP
    # Must inline: A2A_HUB_URL=https://evomap.ai A2A_NODE_ID=evo-shenhai-prod-7f3a9c
    # Must use: nohup $NODE_PATH index.js run --loop > ~/.openclaw/logs/evolver.log 2>&1 &
    # Key trap: must use $NODE_PATH (not bare 'node') for 深海
    shenhai_start_checks = []

    # ssh with CENTRAL_SSH_KEY variable reference
    has_ssh_central_key = bool(re.search(r'ssh\s+.*-i\s+["\']?\$CENTRAL_SSH_KEY["\']?', content))
    shenhai_start_checks.append(f"ssh -i $CENTRAL_SSH_KEY: {'✓' if has_ssh_central_key else '✗'}")

    # root@$CENTRAL_IP
    has_central_ip = bool(re.search(r'root@\$CENTRAL_IP', content))
    shenhai_start_checks.append(f"root@$CENTRAL_IP: {'✓' if has_central_ip else '✗'}")

    # A2A_NODE_ID with correct central node id
    has_central_node_id = bool(re.search(rf'A2A_NODE_ID={re.escape(CENTRAL_NODE_ID)}', content))
    shenhai_start_checks.append(f"A2A_NODE_ID={CENTRAL_NODE_ID}: {'✓' if has_central_node_id else '✗'}")

    # Hub URL
    has_hub_url_central = bool(re.search(rf'A2A_HUB_URL={re.escape(HUB_URL)}', content))
    shenhai_start_checks.append(f"A2A_HUB_URL={HUB_URL}: {'✓' if has_hub_url_central else '✗'}")

    # CRITICAL TRAP: Must use $NODE_PATH (not bare 'node') for 深海 start
    # Look for nohup $NODE_PATH index.js run --loop
    has_node_path_var = bool(re.search(r'nohup\s+\$NODE_PATH\s+index\.js\s+run\s+--loop', content))
    shenhai_start_checks.append(f"nohup $NODE_PATH index.js run --loop (central uses full path): {'✓' if has_node_path_var else '✗'}")

    # Log path
    has_central_log = bool(re.search(r'~/\.openclaw/logs/evolver\.log', content))
    shenhai_start_checks.append(f"log path ~/.openclaw/logs/evolver.log: {'✓' if has_central_log else '✗'}")

    # nohup background with 2>&1 &
    has_nohup_bg = bool(re.search(r'nohup.*2>&1\s*&', content, re.DOTALL))
    shenhai_start_checks.append(f"nohup ... 2>&1 &: {'✓' if has_nohup_bg else '✗'}")

    # cd to correct directory
    has_openclaw_dir = bool(re.search(r'cd\s+~/\.openclaw/evolver', content))
    shenhai_start_checks.append(f"cd ~/.openclaw/evolver: {'✓' if has_openclaw_dir else '✗'}")

    shenhai_passed = all([
        has_ssh_central_key, has_central_ip, has_central_node_id,
        has_hub_url_central, has_node_path_var, has_central_log,
        has_nohup_bg, has_openclaw_dir
    ])
    checks.append({
        "name": "shenhai_node_start_correct",
        "passed": shenhai_passed,
        "detail": "; ".join(shenhai_start_checks)
    })

    # ---- CHECK 3: 泰拉 node start command ----
    # Must use: ssh -i $TOKYO_SSH_KEY root@$TOKYO_IP
    # Must inline: A2A_HUB_URL=https://evomap.ai A2A_NODE_ID=evo-tela-tokyo-2b8d14
    # CRITICAL TRAP: must use bare 'node' (not $NODE_PATH) for 泰拉
    tela_start_checks = []

    has_ssh_tokyo_key = bool(re.search(r'ssh\s+.*-i\s+["\']?\$TOKYO_SSH_KEY["\']?', content))
    tela_start_checks.append(f"ssh -i $TOKYO_SSH_KEY: {'✓' if has_ssh_tokyo_key else '✗'}")

    has_tokyo_ip = bool(re.search(r'root@\$TOKYO_IP', content))
    tela_start_checks.append(f"root@$TOKYO_IP: {'✓' if has_tokyo_ip else '✗'}")

    has_tokyo_node_id = bool(re.search(rf'A2A_NODE_ID={re.escape(TOKYO_NODE_ID)}', content))
    tela_start_checks.append(f"A2A_NODE_ID={TOKYO_NODE_ID}: {'✓' if has_tokyo_node_id else '✗'}")

    # CRITICAL TRAP: 泰拉 uses bare 'node' NOT $NODE_PATH
    # Find the tokyo ssh block and check it uses 'node index.js' not '$NODE_PATH index.js'
    # We look for a pattern: in the context of TOKYO_SSH_KEY or TOKYO_IP, uses 'nohup node index.js run --loop' 
    # (not $NODE_PATH)
    # Strategy: check that there is a line with TOKYO that has 'nohup node index.js' without $NODE_PATH
    has_bare_node_tokyo = bool(re.search(
        r'TOKYO_IP.*?nohup\s+node\s+index\.js\s+run\s+--loop|nohup\s+node\s+index\.js\s+run\s+--loop.*?TOKYO_IP',
        content, re.DOTALL
    ))
    # Also accept if the ssh command to tokyo contains nohup node (not $NODE_PATH)
    # Search within quoted SSH command context for tokyo
    tokyo_ssh_blocks = re.findall(
        r'ssh\s+.*?TOKYO.*?"([^"]*)"',
        content, re.DOTALL
    )
    if not tokyo_ssh_blocks:
        tokyo_ssh_blocks = re.findall(
            r"ssh\s+.*?TOKYO.*?'([^']*)'",
            content, re.DOTALL
        )
    tokyo_bare_node_in_block = any(
        re.search(r'nohup\s+node\s+index\.js', blk) and not re.search(r'nohup\s+\$NODE_PATH', blk)
        for blk in tokyo_ssh_blocks
    )
    # Also check global: if there's a nohup node index.js (bare) and a separate nohup $NODE_PATH
    global_bare_node = bool(re.search(r'nohup\s+node\s+index\.js\s+run\s+--loop', content))
    global_node_path = bool(re.search(r'nohup\s+\$NODE_PATH\s+index\.js\s+run\s+--loop', content))
    tela_uses_bare_node = (tokyo_bare_node_in_block or (global_bare_node and global_node_path))
    tela_start_checks.append(f"nohup node index.js run --loop (bare, not $NODE_PATH for Tokyo): {'✓' if tela_uses_bare_node else '✗'}")

    tela_passed = all([
        has_ssh_tokyo_key, has_tokyo_ip, has_tokyo_node_id, tela_uses_bare_node
    ])
    checks.append({
        "name": "tela_node_start_correct",
        "passed": tela_passed,
        "detail": "; ".join(tela_start_checks)
    })

    # ---- CHECK 4: Status check for all 3 nodes ----
    # 深海: ssh -i $CENTRAL_SSH_KEY root@$CENTRAL_IP "ps aux | grep 'node index.js' | grep -v grep"
    # 泰拉: ssh -i $TOKYO_SSH_KEY root@$TOKYO_IP "ps aux | grep 'node index.js' | grep -v grep"
    # 天空: ps aux | grep "node index.js" | grep -v grep (local, no ssh)
    status_checks = []

    has_status_central = bool(re.search(
        r'ssh\s+.*CENTRAL_SSH_KEY.*CENTRAL_IP.*ps\s+aux.*grep.*node\s+index\.js.*grep\s+-v\s+grep',
        content, re.DOTALL
    ))
    status_checks.append(f"深海 status check (ssh+ps aux+grep): {'✓' if has_status_central else '✗'}")

    has_status_tokyo = bool(re.search(
        r'ssh\s+.*TOKYO_SSH_KEY.*TOKYO_IP.*ps\s+aux.*grep.*node\s+index\.js.*grep\s+-v\s+grep',
        content, re.DOTALL
    ))
    status_checks.append(f"泰拉 status check (ssh+ps aux+grep): {'✓' if has_status_tokyo else '✗'}")

    # 天空 is local - no ssh, just ps aux
    has_status_local = bool(re.search(
        r'(?<!ssh\s)(?<!\$CENTRAL_SSH_KEY\s)ps\s+aux\s*\|\s*grep\s+["\']?node\s+index\.js["\']?\s*\|\s*grep\s+-v\s+grep',
        content
    ))
    status_checks.append(f"天空 status check (local ps aux, no ssh): {'✓' if has_status_local else '✗'}")

    status_passed = has_status_central and has_status_tokyo and has_status_local
    checks.append({
        "name": "all_three_nodes_status_check",
        "passed": status_passed,
        "detail": "; ".join(status_checks)
    })

    # ---- CHECK 5: Stop 泰拉 (Tokyo) only ----
    # ssh -i $TOKYO_SSH_KEY root@$TOKYO_IP "pkill -f 'node index.js'"
    # Must NOT stop 深海 or 天空
    stop_checks = []

    has_stop_tokyo = bool(re.search(
        r'ssh\s+.*TOKYO_SSH_KEY.*TOKYO_IP.*pkill\s+-f\s+["\']?node\s+index\.js["\']?',
        content, re.DOTALL
    ))
    stop_checks.append(f"Stop 泰拉 with pkill via SSH: {'✓' if has_stop_tokyo else '✗'}")

    # Must NOT have stop for central (pkill via CENTRAL_SSH_KEY)
    has_stop_central = bool(re.search(
        r'ssh\s+.*CENTRAL_SSH_KEY.*CENTRAL_IP.*pkill\s+-f',
        content, re.DOTALL
    ))
    no_stop_central = not has_stop_central
    stop_checks.append(f"Does NOT stop 深海: {'✓' if no_stop_central else '✗'}")

    # Must NOT have local pkill (which would stop 天空)
    has_local_pkill = bool(re.search(
        r'(?<!ssh[^\n]{0,200})pkill\s+-f\s+["\']?node\s+index\.js["\']?(?![^\n]*TOKYO)(?![^\n]*CENTRAL)',
        content
    ))
    # More robust: look for pkill -f that is NOT wrapped in an ssh command
    lines = content.split('\n')
    local_pkill_found = False
    for line in lines:
        stripped = line.strip()
        if re.search(r'pkill\s+-f\s+["\']?node\s+index\.js["\']?', stripped):
            if not re.search(r'\$CENTRAL_SSH_KEY|\$TOKYO_SSH_KEY', stripped):
                # might be inside an ssh string though
                if not re.search(r'^ssh\s+', stripped):
                    local_pkill_found = True
                    break

    no_stop_tiankong = not local_pkill_found
    stop_checks.append(f"Does NOT stop 天空 (no local pkill): {'✓' if no_stop_tiankong else '✗'}")

    stop_passed = has_stop_tokyo and no_stop_central and no_stop_tiankong
    checks.append({
        "name": "stop_only_tela_node",
        "passed": stop_passed,
        "detail": "; ".join(stop_checks)
    })

    # ---- CHECK 6: Script ordering (start → status → stop) ----
    order_checks = []
    try:
        # Find positions of key operations
        pos_start_shenhai = content.find(CENTRAL_NODE_ID)
        pos_start_tela = content.find(TOKYO_NODE_ID)
        
        # Find first status check
        ps_aux_match = list(re.finditer(r'ps\s+aux', content))
        pos_first_status = ps_aux_match[0].start() if ps_aux_match else -1
        
        # Find stop command
        stop_match = re.search(r'pkill\s+-f\s+["\']?node\s+index\.js["\']?', content)
        pos_stop = stop_match.start() if stop_match else -1

        all_found = pos_start_shenhai > 0 and pos_start_tela > 0 and pos_first_status > 0 and pos_stop > 0
        if all_found:
            # Starts should come before status checks
            start_before_status = (pos_start_shenhai < pos_first_status and pos_start_tela < pos_first_status)
            # Status checks before stop
            status_before_stop = pos_first_status < pos_stop
            order_ok = start_before_status and status_before_stop
            order_checks.append(f"start→status→stop ordering: {'✓' if order_ok else '✗'} "
                                 f"(start_shenhai@{pos_start_shenhai}, start_tela@{pos_start_tela}, "
                                 f"first_status@{pos_first_status}, stop@{pos_stop})")
        else:
            order_ok = False
            order_checks.append(f"Could not verify ordering: some commands missing")
    except Exception as e:
        order_ok = False
        order_checks.append(f"Order check error: {e}")

    checks.append({
        "name": "correct_operation_ordering",
        "passed": order_ok,
        "detail": "; ".join(order_checks)
    })

    # ---- OVERALL SCORING ----
    check_weights = {
        "file_exists": 0.05,
        "file_readable": 0.05,
        "env_vars_correctly_set": 0.15,
        "shenhai_node_start_correct": 0.25,  # Highest weight - contains the proprietary trap
        "tela_node_start_correct": 0.20,
        "all_three_nodes_status_check": 0.15,
        "stop_only_tela_node": 0.10,
        "correct_operation_ordering": 0.05,
    }

    total_score = 0.0
    for check in checks:
        weight = check_weights.get(check["name"], 0.0)
        if check["passed"]:
            total_score += weight

    all_critical = (
        checks[2]["passed"] and  # env vars
        checks[3]["passed"] and  # shenhai start (contains $NODE_PATH trap)
        checks[4]["passed"] and  # tela start (bare node trap)
        checks[5]["passed"] and  # status check all 3
        checks[6]["passed"]      # stop only tela
    )

    return {
        "passed": all_critical,
        "score": round(total_score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "invocation", "passed": False, "detail": "Usage: eval_script.py <workspace_dir>"}
        ]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))