import sys
import json
import os
from pathlib import Path

def load_config(workspace):
    config_path = Path(workspace) / "openclaw.json"
    with open(config_path, "r") as f:
        return json.load(f)

def run_checks(workspace):
    checks = []
    
    # ── Load config ────────────────────────────────────────────────────────
    try:
        cfg = load_config(workspace)
    except FileNotFoundError:
        return [{"name": "config_file_exists", "passed": False, "detail": "openclaw.json not found"}]
    except json.JSONDecodeError as e:
        return [{"name": "config_file_valid_json", "passed": False, "detail": f"JSON parse error: {e}"}]

    checks.append({"name": "config_file_exists_and_valid", "passed": True, "detail": "openclaw.json found and valid JSON"})

    # ── Expected values ────────────────────────────────────────────────────
    EXPECTED_AGENTS = {
        "orchestrator":      ("cli_LegalOrch001",  "sOrc_X9k2mP4nQ7rT"),
        "contract-reviewer": ("cli_ContractRev002", "sCR_Yn3vB8wL5jK1d"),
        "legal-researcher":  ("cli_LegalRes003",    "sLR_Zm6uD9xN2cH4f"),
        "case-manager":      ("cli_CaseMgr004",     "sCM_Wq7eG1yO3iJ5g"),
    }
    SPECIALIST_IDS = ["contract-reviewer", "legal-researcher", "case-manager"]

    # ── Check 1: All four accounts present in channels.feishu.accounts ─────
    try:
        accounts = cfg["channels"]["feishu"]["accounts"]
        account_keys = set(accounts.keys())
        # Find account keys that map to each expected agent
        agent_to_account_key = {}
        for key, val in accounts.items():
            agent_id = val.get("agent")
            if agent_id in EXPECTED_AGENTS:
                agent_to_account_key[agent_id] = key

        missing_agents_in_accounts = [a for a in EXPECTED_AGENTS if a not in agent_to_account_key]
        if missing_agents_in_accounts:
            checks.append({
                "name": "all_four_accounts_present",
                "passed": False,
                "detail": f"Missing accounts for agents: {missing_agents_in_accounts}"
            })
        else:
            checks.append({
                "name": "all_four_accounts_present",
                "passed": True,
                "detail": f"All four accounts present. accountId keys: {list(agent_to_account_key.values())}"
            })
    except (KeyError, TypeError) as e:
        checks.append({"name": "all_four_accounts_present", "passed": False, "detail": f"Structure error: {e}"})
        agent_to_account_key = {}
        accounts = {}

    # ── Check 2: Correct AppID and AppSecret in each account ───────────────
    credential_errors = []
    for agent_id, (expected_app_id, expected_secret) in EXPECTED_AGENTS.items():
        key = agent_to_account_key.get(agent_id)
        if key is None:
            credential_errors.append(f"{agent_id}: no account key found")
            continue
        entry = accounts.get(key, {})
        actual_app_id = entry.get("appId", "")
        actual_secret = entry.get("appSecret", "")
        if actual_app_id != expected_app_id:
            credential_errors.append(f"{agent_id}: appId expected={expected_app_id} got={actual_app_id}")
        if actual_secret != expected_secret:
            credential_errors.append(f"{agent_id}: appSecret expected={expected_secret} got={actual_secret}")

    if credential_errors:
        checks.append({"name": "correct_credentials", "passed": False, "detail": "; ".join(credential_errors)})
    else:
        checks.append({"name": "correct_credentials", "passed": True, "detail": "All AppIDs and AppSecrets match requirements"})

    # ── Check 3: account.agent field matches agent id in agents.list ───────
    agent_field_errors = []
    for agent_id in EXPECTED_AGENTS:
        key = agent_to_account_key.get(agent_id)
        if key:
            declared_agent = accounts.get(key, {}).get("agent", "")
            if declared_agent != agent_id:
                agent_field_errors.append(f"account key '{key}': agent field='{declared_agent}' expected='{agent_id}'")

    if agent_field_errors:
        checks.append({"name": "account_agent_field_consistency", "passed": False, "detail": "; ".join(agent_field_errors)})
    else:
        checks.append({"name": "account_agent_field_consistency", "passed": True, "detail": "All account.agent fields correctly reference their agent IDs"})

    # ── Check 4: Bindings use type "route" (not "delivery" or other) ───────
    try:
        bindings = cfg["bindings"]
        wrong_type = [b for b in bindings if b.get("type") != "route"]
        if wrong_type:
            checks.append({
                "name": "binding_type_is_route",
                "passed": False,
                "detail": f"{len(wrong_type)} binding(s) have wrong type: {[b.get('type') for b in wrong_type]}"
            })
        else:
            checks.append({
                "name": "binding_type_is_route",
                "passed": True,
                "detail": f"All {len(bindings)} bindings use type='route'"
            })
    except (KeyError, TypeError) as e:
        checks.append({"name": "binding_type_is_route", "passed": False, "detail": f"Cannot read bindings: {e}"})
        bindings = []

    # ── Check 5: All four agents have bindings ──────────────────────────────
    try:
        bound_account_ids = {b["match"]["accountId"] for b in bindings if "match" in b}
        bound_agents = set()
        for b in bindings:
            bound_agents.add(b.get("agent"))
        
        # Verify each expected agent is reachable via a binding
        unbound_agents = [a for a in EXPECTED_AGENTS if a not in bound_agents]
        if unbound_agents:
            checks.append({
                "name": "all_four_agents_have_bindings",
                "passed": False,
                "detail": f"No binding found for agents: {unbound_agents}"
            })
        else:
            checks.append({
                "name": "all_four_agents_have_bindings",
                "passed": True,
                "detail": "All four agents have at least one binding"
            })
    except Exception as e:
        checks.append({"name": "all_four_agents_have_bindings", "passed": False, "detail": f"Error: {e}"})

    # ── Check 6: accountId consistency — binding.match.accountId matches account key ──
    try:
        account_keys_set = set(accounts.keys())
        inconsistent = []
        for b in bindings:
            bid = b.get("match", {}).get("accountId")
            if bid and bid not in account_keys_set:
                inconsistent.append(bid)
        if inconsistent:
            checks.append({
                "name": "accountId_consistency_bindings_vs_accounts",
                "passed": False,
                "detail": f"Binding accountIds not found in accounts keys: {inconsistent}"
            })
        else:
            checks.append({
                "name": "accountId_consistency_bindings_vs_accounts",
                "passed": True,
                "detail": "All binding accountIds match keys in channels.feishu.accounts"
            })
    except Exception as e:
        checks.append({"name": "accountId_consistency_bindings_vs_accounts", "passed": False, "detail": f"Error: {e}"})

    # ── Check 7: All four agents present in agents.list ────────────────────
    try:
        agents_list = cfg["agents"]["list"]
        agent_ids_in_list = {a["id"] for a in agents_list}
        missing_from_list = [a for a in EXPECTED_AGENTS if a not in agent_ids_in_list]
        if missing_from_list:
            checks.append({
                "name": "all_four_agents_in_agents_list",
                "passed": False,
                "detail": f"Missing from agents.list: {missing_from_list}"
            })
        else:
            checks.append({
                "name": "all_four_agents_in_agents_list",
                "passed": True,
                "detail": "All four agents defined in agents.list"
            })
    except (KeyError, TypeError) as e:
        checks.append({"name": "all_four_agents_in_agents_list", "passed": False, "detail": f"Structure error: {e}"})
        agents_list = []
        agent_ids_in_list = set()

    # ── Check 8: orchestrator.allowAgents contains all three specialists ───
    try:
        orchestrator_entry = next((a for a in agents_list if a.get("id") == "orchestrator"), None)
        if orchestrator_entry is None:
            checks.append({
                "name": "orchestrator_allow_agents_complete",
                "passed": False,
                "detail": "orchestrator not found in agents.list"
            })
        else:
            allow = set(orchestrator_entry.get("allowAgents", []))
            missing_from_allow = [s for s in SPECIALIST_IDS if s not in allow]
            if missing_from_allow:
                checks.append({
                    "name": "orchestrator_allow_agents_complete",
                    "passed": False,
                    "detail": f"orchestrator.allowAgents missing: {missing_from_allow}. Has: {list(allow)}"
                })
            else:
                checks.append({
                    "name": "orchestrator_allow_agents_complete",
                    "passed": True,
                    "detail": f"orchestrator.allowAgents includes all three specialists: {list(allow)}"
                })
    except Exception as e:
        checks.append({"name": "orchestrator_allow_agents_complete", "passed": False, "detail": f"Error: {e}"})

    # ── Check 9: agentToAgent.enabled is false (known bug #5813) ────────────
    try:
        ata = cfg.get("gateway", {}).get("agentToAgent", {})
        enabled = ata.get("enabled", False)
        if enabled is True:
            checks.append({
                "name": "agentToAgent_disabled",
                "passed": False,
                "detail": f"gateway.agentToAgent.enabled is True — this breaks sub-agent spawning (bug #5813)"
            })
        else:
            checks.append({
                "name": "agentToAgent_disabled",
                "passed": True,
                "detail": f"gateway.agentToAgent.enabled is {enabled!r} (not True) — correct"
            })
    except Exception as e:
        # If the key doesn't exist at all, that's fine (defaults to false)
        checks.append({
            "name": "agentToAgent_disabled",
            "passed": True,
            "detail": f"agentToAgent key absent (defaults to disabled): {e}"
        })

    # ── Check 10: No leftover PLACEHOLDER credentials ───────────────────────
    try:
        placeholder_found = []
        for key, val in accounts.items():
            if "PLACEHOLDER" in str(val.get("appId", "")) or "PLACEHOLDER" in str(val.get("appSecret", "")):
                placeholder_found.append(key)
        if placeholder_found:
            checks.append({
                "name": "no_placeholder_credentials",
                "passed": False,
                "detail": f"Accounts still have PLACEHOLDER credentials: {placeholder_found}"
            })
        else:
            checks.append({
                "name": "no_placeholder_credentials",
                "passed": True,
                "detail": "No PLACEHOLDER credentials found"
            })
    except Exception as e:
        checks.append({"name": "no_placeholder_credentials", "passed": False, "detail": f"Error: {e}"})

    return checks


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = run_checks(workspace)
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4) if total > 0 else 0.0
    all_passed = passed_count == total
    result = {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()