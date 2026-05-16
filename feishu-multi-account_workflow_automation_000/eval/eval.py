import sys
import json
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    
    config_path = Path(workspace) / "openclaw.json"
    
    # --- Load file ---
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "config_file_exists", "passed": False, "detail": "openclaw.json not found at workspace root"}]
        }
    except json.JSONDecodeError as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "config_file_valid_json", "passed": False, "detail": f"JSON parse error: {e}"}]
        }

    # CHECK 1: 'bindings' exists at top level
    has_top_level_bindings = "bindings" in config and isinstance(config["bindings"], list)
    checks.append({
        "name": "bindings_at_top_level",
        "passed": has_top_level_bindings,
        "detail": f"'bindings' key at top-level: {'found' if has_top_level_bindings else 'MISSING or misplaced'}"
    })

    # CHECK 2: 'routing' (wrong key) should NOT exist at top level or inside channels
    routing_in_channels = "routing" in config.get("channels", {}).get("feishu", {})
    routing_at_top = "routing" in config
    no_wrong_routing_key = not routing_in_channels and not routing_at_top
    checks.append({
        "name": "no_wrong_routing_key",
        "passed": no_wrong_routing_key,
        "detail": f"Wrong 'routing' key removed: channels.feishu.routing={'present (BAD)' if routing_in_channels else 'absent (OK)'}, top-level routing={'present (BAD)' if routing_at_top else 'absent (OK)'}"
    })

    # CHECK 3: bindings has entry for 'main' account with correct fields
    bindings = config.get("bindings", [])
    main_binding = next((b for b in bindings if isinstance(b, dict) and b.get("agentId") == "main" and isinstance(b.get("match"), dict) and b["match"].get("channel") == "feishu" and b["match"].get("accountId") == "main"), None)
    checks.append({
        "name": "binding_for_main_account",
        "passed": main_binding is not None,
        "detail": f"Binding for main account (agentId='main', match.channel='feishu', match.accountId='main'): {'found' if main_binding else 'MISSING'}"
    })

    # CHECK 4: bindings has entry for 'sub1' account with correct fields
    sub1_binding = next((b for b in bindings if isinstance(b, dict) and b.get("agentId") == "sub1" and isinstance(b.get("match"), dict) and b["match"].get("channel") == "feishu" and b["match"].get("accountId") == "sub1"), None)
    checks.append({
        "name": "binding_for_sub1_account",
        "passed": sub1_binding is not None,
        "detail": f"Binding for sub1 account (agentId='sub1', match.channel='feishu', match.accountId='sub1'): {'found' if sub1_binding else 'MISSING'}"
    })

    # CHECK 5: bindings use 'accountId' not 'account'
    bad_account_key = any(
        isinstance(b.get("match"), dict) and "account" in b["match"] and "accountId" not in b["match"]
        for b in bindings if isinstance(b, dict)
    )
    checks.append({
        "name": "bindings_use_accountId_not_account",
        "passed": not bad_account_key,
        "detail": f"All bindings use 'accountId' (not 'account'): {'YES' if not bad_account_key else 'NO - found wrong key name'}"
    })

    # CHECK 6: agents.list contains main agent with default: true
    agents_list = config.get("agents", {}).get("list", [])
    main_agent = next((a for a in agents_list if isinstance(a, dict) and a.get("id") == "main"), None)
    main_has_default = main_agent is not None and main_agent.get("default") is True
    checks.append({
        "name": "main_agent_has_default_true",
        "passed": main_has_default,
        "detail": f"agents.list main agent has 'default: true': {'YES' if main_has_default else 'NO'}"
    })

    # CHECK 7: agents.list contains sub1 agent with a workspace field
    sub1_agent = next((a for a in agents_list if isinstance(a, dict) and a.get("id") == "sub1"), None)
    sub1_has_workspace = sub1_agent is not None and "workspace" in sub1_agent and isinstance(sub1_agent["workspace"], str) and len(sub1_agent["workspace"]) > 0
    checks.append({
        "name": "sub1_agent_has_workspace",
        "passed": sub1_has_workspace,
        "detail": f"agents.list sub1 agent has non-empty 'workspace': {'YES ('+sub1_agent['workspace']+')' if sub1_has_workspace else 'NO'}"
    })

    # CHECK 8: channels.feishu.accounts has both 'main' and 'sub1' with appId and appSecret
    feishu_accounts = config.get("channels", {}).get("feishu", {}).get("accounts", {})
    main_account_ok = (
        "main" in feishu_accounts and
        "appId" in feishu_accounts["main"] and
        "appSecret" in feishu_accounts["main"]
    )
    sub1_account_ok = (
        "sub1" in feishu_accounts and
        "appId" in feishu_accounts["sub1"] and
        "appSecret" in feishu_accounts["sub1"]
    )
    accounts_ok = main_account_ok and sub1_account_ok
    checks.append({
        "name": "feishu_accounts_have_credentials",
        "passed": accounts_ok,
        "detail": f"feishu accounts main OK: {main_account_ok}, sub1 OK: {sub1_account_ok}"
    })

    # CHECK 9: channels.feishu.accounts has 'default' policy sub-key with groupPolicy and dmPolicy
    default_policy = feishu_accounts.get("default", {})
    has_group_policy = isinstance(default_policy, dict) and "groupPolicy" in default_policy
    has_dm_policy = isinstance(default_policy, dict) and "dmPolicy" in default_policy
    default_policy_ok = has_group_policy and has_dm_policy
    checks.append({
        "name": "feishu_accounts_default_policy_present",
        "passed": default_policy_ok,
        "detail": f"channels.feishu.accounts.default has groupPolicy: {has_group_policy}, dmPolicy: {has_dm_policy}"
    })

    # CHECK 10: Original non-feishu config preserved (server port, logging)
    server_ok = config.get("server", {}).get("port") == 8080
    logging_ok = config.get("logging", {}).get("level") == "info"
    preservation_ok = server_ok and logging_ok
    checks.append({
        "name": "original_config_fields_preserved",
        "passed": preservation_ok,
        "detail": f"server.port=8080: {server_ok}, logging.level=info: {logging_ok}"
    })

    # Score
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4)
    all_passed = passed_count == total

    return {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2, ensure_ascii=False))