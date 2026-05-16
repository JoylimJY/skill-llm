#!/usr/bin/env python3
import json
import os
import sys
import glob
from pathlib import Path

HOME = os.path.expanduser("~")
OPENCLAW_DIR = os.path.join(HOME, ".openclaw")
CONFIG_PATH = os.path.join(OPENCLAW_DIR, "openclaw.json")
DEVOPS_CHAT_ID = "oc_d3f4a8b2c1e5f6a7b8c9d0e1"
DEVOPS_AGENT_ID = "devops"

checks = []

def check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return passed

# ---- Load config ----
try:
    with open(CONFIG_PATH) as f:
        config = json.load(f)
except Exception as e:
    check("config_readable", False, f"Cannot read openclaw.json: {e}")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

check("config_readable", True, "openclaw.json is valid JSON")

# ---- CHECK 1: Devops workspace is NOT the shared main workspace ----
try:
    agents = config.get("agents", {}).get("list", [])
    devops_agent = next((a for a in agents if a["id"] == DEVOPS_AGENT_ID), None)
    if devops_agent is None:
        check("devops_workspace_isolated", False, "devops agent not found in agents.list")
    else:
        ws = devops_agent.get("workspace", "")
        shared_ws = os.path.join(OPENCLAW_DIR, "workspace")
        # Must NOT point to the shared main workspace
        is_isolated = (ws != shared_ws and DEVOPS_AGENT_ID in ws)
        check(
            "devops_workspace_isolated",
            is_isolated,
            f"devops workspace='{ws}', shared main='{shared_ws}'. Must be a dedicated, separate path containing 'devops'."
        )
except Exception as e:
    check("devops_workspace_isolated", False, f"Error checking workspace: {e}")

# ---- CHECK 2: Dedicated workspace directory exists ----
try:
    devops_agent = next((a for a in config.get("agents", {}).get("list", []) if a["id"] == DEVOPS_AGENT_ID), None)
    if devops_agent:
        ws_path = devops_agent.get("workspace", "")
        ws_exists = os.path.isdir(ws_path)
        check("devops_workspace_dir_exists", ws_exists, f"Directory '{ws_path}' exists: {ws_exists}")
    else:
        check("devops_workspace_dir_exists", False, "devops agent not found")
except Exception as e:
    check("devops_workspace_dir_exists", False, f"Error: {e}")

# ---- CHECK 3: SOUL.md exists in devops workspace ----
try:
    devops_agent = next((a for a in config.get("agents", {}).get("list", []) if a["id"] == DEVOPS_AGENT_ID), None)
    if devops_agent:
        ws_path = devops_agent.get("workspace", "")
        soul_path = os.path.join(ws_path, "SOUL.md")
        soul_exists = os.path.isfile(soul_path)
        soul_nonempty = soul_exists and os.path.getsize(soul_path) > 0
        check("soul_md_in_devops_workspace", soul_nonempty, f"SOUL.md at '{soul_path}': exists={soul_exists}, non-empty={soul_nonempty}")
    else:
        check("soul_md_in_devops_workspace", False, "devops agent not found")
except Exception as e:
    check("soul_md_in_devops_workspace", False, f"Error: {e}")

# ---- CHECK 4: AGENTS.md exists in devops workspace ----
try:
    devops_agent = next((a for a in config.get("agents", {}).get("list", []) if a["id"] == DEVOPS_AGENT_ID), None)
    if devops_agent:
        ws_path = devops_agent.get("workspace", "")
        agents_path = os.path.join(ws_path, "AGENTS.md")
        agents_exists = os.path.isfile(agents_path)
        agents_nonempty = agents_exists and os.path.getsize(agents_path) > 0
        check("agents_md_in_devops_workspace", agents_nonempty, f"AGENTS.md at '{agents_path}': exists={agents_exists}, non-empty={agents_nonempty}")
    else:
        check("agents_md_in_devops_workspace", False, "devops agent not found")
except Exception as e:
    check("agents_md_in_devops_workspace", False, f"Error: {e}")

# ---- CHECK 5: Devops group is in channels.feishu.groups ----
try:
    groups = config.get("channels", {}).get("feishu", {}).get("groups", {})
    has_group = DEVOPS_CHAT_ID in groups
    check(
        "devops_group_in_feishu_channels",
        has_group,
        f"channels.feishu.groups contains '{DEVOPS_CHAT_ID}': {has_group}. groups keys: {list(groups.keys())}"
    )
except Exception as e:
    check("devops_group_in_feishu_channels", False, f"Error: {e}")

# ---- CHECK 6: Binding exists for devops -> devops chat group ----
try:
    bindings = config.get("bindings", [])
    devops_binding = None
    for b in bindings:
        if (b.get("agentId") == DEVOPS_AGENT_ID and
                b.get("match", {}).get("channel") == "feishu" and
                b.get("match", {}).get("peer", {}).get("id") == DEVOPS_CHAT_ID and
                b.get("match", {}).get("peer", {}).get("kind") == "group"):
            devops_binding = b
            break
    check(
        "devops_binding_exists",
        devops_binding is not None,
        f"Binding for agentId=devops, channel=feishu, peer.id={DEVOPS_CHAT_ID}, peer.kind=group found: {devops_binding is not None}"
    )
except Exception as e:
    check("devops_binding_exists", False, f"Error: {e}")

# ---- CHECK 7: CRITICAL — accountId is "main" in devops binding ----
try:
    bindings = config.get("bindings", [])
    devops_binding = None
    for b in bindings:
        if (b.get("agentId") == DEVOPS_AGENT_ID and
                b.get("match", {}).get("peer", {}).get("id") == DEVOPS_CHAT_ID):
            devops_binding = b
            break
    if devops_binding is None:
        check("binding_accountId_is_main", False, "devops binding not found — cannot check accountId")
    else:
        account_id = devops_binding.get("match", {}).get("accountId", "")
        is_main = (account_id == "main")
        check(
            "binding_accountId_is_main",
            is_main,
            f"binding.match.accountId='{account_id}', expected 'main'. "
            f"(If 'main' is missing, binding is silently ignored at route time.)"
        )
except Exception as e:
    check("binding_accountId_is_main", False, f"Error: {e}")

# ---- CHECK 8: accountId is NOT set to the chat_id (CLI pitfall guard) ----
try:
    bindings = config.get("bindings", [])
    devops_binding = None
    for b in bindings:
        if b.get("agentId") == DEVOPS_AGENT_ID:
            devops_binding = b
            break
    if devops_binding is None:
        check("binding_accountId_not_chat_id", False, "devops binding not found")
    else:
        account_id = devops_binding.get("match", {}).get("accountId", "")
        not_chat_id = (account_id != DEVOPS_CHAT_ID)
        check(
            "binding_accountId_not_chat_id",
            not_chat_id,
            f"accountId='{account_id}'. Must NOT equal chat_id '{DEVOPS_CHAT_ID}' (that is the broken CLI pitfall)."
        )
except Exception as e:
    check("binding_accountId_not_chat_id", False, f"Error: {e}")

# ---- CHECK 9: Stale sessions for DEVOPS_CHAT_ID removed from HR agent ----
try:
    hr_sessions_path = os.path.join(OPENCLAW_DIR, "agents", "hr", "sessions", "sessions.json")
    with open(hr_sessions_path) as f:
        hr_sessions = json.load(f)
    stale_keys = [k for k in hr_sessions if DEVOPS_CHAT_ID in k]
    cleaned = len(stale_keys) == 0
    check(
        "stale_sessions_cleaned",
        cleaned,
        f"Stale session keys containing '{DEVOPS_CHAT_ID}' in HR sessions: {stale_keys}. "
        f"All must be removed."
    )
except Exception as e:
    check("stale_sessions_cleaned", False, f"Error reading HR sessions: {e}")

# ---- CHECK 10: HR binding for HR group still intact ----
try:
    bindings = config.get("bindings", [])
    HR_CHAT_ID = "oc_a1b2c3d4e5f6a7b8c9d0e1f2"
    hr_binding = next(
        (b for b in bindings
         if b.get("agentId") == "hr" and
         b.get("match", {}).get("peer", {}).get("id") == HR_CHAT_ID),
        None
    )
    check(
        "hr_binding_preserved",
        hr_binding is not None,
        f"Original HR binding for group '{HR_CHAT_ID}' still present: {hr_binding is not None}"
    )
except Exception as e:
    check("hr_binding_preserved", False, f"Error: {e}")

# ---- CHECK 11: Gateway restart was triggered ----
try:
    restart_marker = os.path.join(OPENCLAW_DIR, ".gateway_restart_marker")
    restarted = os.path.isfile(restart_marker)
    check(
        "gateway_restarted",
        restarted,
        f"Gateway restart marker found at '{restart_marker}': {restarted}"
    )
except Exception as e:
    check("gateway_restarted", False, f"Error: {e}")

# ---- Scoring ----
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 4)

# Critical checks: binding_accountId_is_main, stale_sessions_cleaned, devops_workspace_isolated
critical_names = {
    "binding_accountId_is_main",
    "stale_sessions_cleaned",
    "devops_workspace_isolated",
    "devops_binding_exists"
}
critical_passed = all(c["passed"] for c in checks if c["name"] in critical_names)
overall_passed = critical_passed and (passed_count >= total * 0.8)

result = {
    "passed": overall_passed,
    "score": score,
    "checks": checks
}

print(json.dumps(result, indent=2, ensure_ascii=False))