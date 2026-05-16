#!/usr/bin/env python3
"""
Evaluation script for openclaw-create-agent task.

Checks:
1. The new agent runtime was created via CLI (agents.json updated)
2. openclaw.json has the new peer binding with correct fields
3. dmScope = per-account-channel-peer (enforced)
4. Existing ops-assistant agent/account/binding is preserved
5. Gateway restart was executed
6. --non-interactive flag was used (checked via mock CLI log)
"""

import json
import sys
from pathlib import Path

OPENCLAW_DIR = Path("/root/.openclaw")
CONFIG_PATH = OPENCLAW_DIR / "openclaw.json"
AGENTS_PATH = OPENCLAW_DIR / "agents.json"
CLI_LOG_PATH = OPENCLAW_DIR / "mock_cli.log"
GATEWAY_STATE_PATH = OPENCLAW_DIR / "gateway_state"

TARGET_AGENT_ID = "logistics-group-bot"
TARGET_PEER_ID = "oc_logistics_team_42x"
TARGET_PEER_KIND = "group"
TARGET_WORKSPACE = "/workspace/agents/logistics-group-bot"

checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return passed


def main():
    # --- Check 1: New agent created in agents.json via CLI ---
    try:
        with open(AGENTS_PATH) as f:
            agents_data = json.load(f)
        agents = {a["id"]: a for a in agents_data.get("agents", [])}
        if TARGET_AGENT_ID in agents:
            agent = agents[TARGET_AGENT_ID]
            ws_ok = agent.get("workspace") == TARGET_WORKSPACE
            add_check(
                "new_agent_in_agents_json",
                True,
                f"Agent '{TARGET_AGENT_ID}' found in agents.json. workspace={'correct' if ws_ok else 'WRONG: ' + str(agent.get('workspace'))}"
            )
        else:
            add_check(
                "new_agent_in_agents_json",
                False,
                f"Agent '{TARGET_AGENT_ID}' NOT found in agents.json. Present agents: {list(agents.keys())}"
            )
    except Exception as e:
        add_check("new_agent_in_agents_json", False, f"Exception reading agents.json: {e}")

    # --- Check 2: --non-interactive flag was used ---
    try:
        log_content = CLI_LOG_PATH.read_text()
        if f"agents add {TARGET_AGENT_ID}" in log_content and "--non-interactive" in log_content:
            add_check("non_interactive_flag_used", True, "--non-interactive flag found in CLI log for the correct agent add command.")
        else:
            # Check if the command was called at all
            if f"agents add {TARGET_AGENT_ID}" in log_content:
                add_check("non_interactive_flag_used", False, f"agents add {TARGET_AGENT_ID} was called but --non-interactive flag was NOT used.")
            else:
                add_check("non_interactive_flag_used", False, f"agents add {TARGET_AGENT_ID} was NOT found in CLI log at all. Log excerpt: {log_content[:500]}")
    except Exception as e:
        add_check("non_interactive_flag_used", False, f"Exception reading CLI log: {e}")

    # --- Check 3: openclaw.json has new peer binding ---
    try:
        with open(CONFIG_PATH) as f:
            config = json.load(f)

        bindings = config.get("bindings", [])
        target_bindings = [
            b for b in bindings
            if b.get("agent_id") == TARGET_AGENT_ID
            and b.get("channel") == "feishu"
            and b.get("routing_mode") == "peer"
        ]

        if not target_bindings:
            add_check(
                "peer_binding_exists",
                False,
                f"No peer binding found for agent '{TARGET_AGENT_ID}' in feishu channel. All bindings: {bindings}"
            )
        else:
            b = target_bindings[0]
            peer_id_ok = b.get("peer_id") == TARGET_PEER_ID
            peer_kind_ok = b.get("peer_kind") == TARGET_PEER_KIND
            detail = (
                f"binding found: {b}. "
                f"peer_id={'OK' if peer_id_ok else 'WRONG: got ' + str(b.get('peer_id'))}. "
                f"peer_kind={'OK' if peer_kind_ok else 'WRONG: got ' + str(b.get('peer_kind'))}."
            )
            add_check("peer_binding_exists", peer_id_ok and peer_kind_ok, detail)
    except Exception as e:
        add_check("peer_binding_exists", False, f"Exception reading config: {e}")

    # --- Check 4: dmScope enforced ---
    try:
        with open(CONFIG_PATH) as f:
            config = json.load(f)
        dm_scope = config.get("session", {}).get("dmScope")
        expected = "per-account-channel-peer"
        if dm_scope == expected:
            add_check("dm_scope_enforced", True, f"dmScope correctly set to '{expected}'")
        else:
            add_check("dm_scope_enforced", False, f"dmScope is '{dm_scope}', expected '{expected}'")
    except Exception as e:
        add_check("dm_scope_enforced", False, f"Exception reading config for dmScope: {e}")

    # --- Check 5: Existing ops-assistant agent/account/binding preserved ---
    try:
        with open(CONFIG_PATH) as f:
            config = json.load(f)

        bindings = config.get("bindings", [])
        ops_binding = [
            b for b in bindings
            if b.get("agent_id") == "ops-assistant"
            and b.get("channel") == "feishu"
            and b.get("routing_mode") == "account"
            and b.get("account_id") == "acct-ops-001"
        ]
        ops_account = config.get("channels", {}).get("feishu", {}).get("accounts", {}).get("acct-ops-001")
        agents_data = json.loads(AGENTS_PATH.read_text())
        ops_in_agents = any(a["id"] == "ops-assistant" for a in agents_data.get("agents", []))

        ok = bool(ops_binding) and ops_account is not None and ops_in_agents
        add_check(
            "existing_agent_preserved",
            ok,
            f"ops-assistant binding present={bool(ops_binding)}, "
            f"acct-ops-001 account present={ops_account is not None}, "
            f"ops-assistant in agents.json={ops_in_agents}"
        )
    except Exception as e:
        add_check("existing_agent_preserved", False, f"Exception checking preserved state: {e}")

    # --- Check 6: Gateway restart was executed ---
    try:
        if GATEWAY_STATE_PATH.exists():
            state = GATEWAY_STATE_PATH.read_text()
            if "gateway_restarted=true" in state:
                add_check("gateway_restarted", True, "Gateway restart command was executed.")
            else:
                add_check("gateway_restarted", False, f"Gateway state file exists but does not contain restart marker: {state}")
        else:
            # Check CLI log as fallback
            log_content = CLI_LOG_PATH.read_text() if CLI_LOG_PATH.exists() else ""
            if "gateway restart" in log_content:
                add_check("gateway_restarted", True, "Gateway restart found in CLI log.")
            else:
                add_check("gateway_restarted", False, "No gateway restart found (state file absent, not in CLI log).")
    except Exception as e:
        add_check("gateway_restarted", False, f"Exception checking gateway state: {e}")

    # --- Check 7: Config file was backed up ---
    try:
        backups = list(OPENCLAW_DIR.glob("openclaw.json.bak.*"))
        if backups:
            add_check("config_backed_up", True, f"Backup found: {[str(b) for b in backups]}")
        else:
            add_check("config_backed_up", False, "No backup file found matching openclaw.json.bak.*")
    except Exception as e:
        add_check("config_backed_up", False, f"Exception checking backups: {e}")

    # --- Scoring ---
    num_passed = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(num_passed / total, 4) if total > 0 else 0.0
    all_passed = all(c["passed"] for c in checks)

    result = {
        "passed": all_passed,
        "score": score,
        "checks": checks,
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()