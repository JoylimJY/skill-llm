#!/usr/bin/env python3
"""
Evaluation script for the OpenClaw agent-creator task.
Target: agent-support  (agentId = "agent-support")
Feishu: accountId=supportbot, botName="Support Dragon", appId=cli_support123, appSecret=s3cr3tXYZ
"""

import sys
import json
import os
from pathlib import Path

AGENT_ID = "agent-support"
HOME = Path("/home/axelhu")
OPENCLAW = HOME / ".openclaw"
WORKSPACE = OPENCLAW / f"workspace-{AGENT_ID}"
AGENTS_DIR = OPENCLAW / "agents" / AGENT_ID
TEMPLATES_DIR = OPENCLAW / "skills" / "agent-creator" / "templates"

FEISHU_ACCOUNT_ID = "supportbot"
FEISHU_BOT_NAME = "Support Dragon"
FEISHU_APP_ID = "cli_support123"
FEISHU_APP_SECRET = "s3cr3tXYZ"
PROVIDER = "anthropic"
MODEL_ID = "claude-3-5-sonnet"
EXPECTED_MODEL_PRIMARY = f"{PROVIDER}/{MODEL_ID}"

checks = []

def check(name: str, passed: bool, detail: str):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return passed


# ── CHECK 1: workspace directory exists ───────────────────────────────────────
try:
    ok = WORKSPACE.is_dir()
    check("workspace_dir_exists",
          ok,
          f"{WORKSPACE} {'exists' if ok else 'MISSING'}")
except Exception as e:
    check("workspace_dir_exists", False, str(e))

# ── CHECK 2: workspace/agent sub-directory exists ─────────────────────────────
try:
    agent_subdir = WORKSPACE / "agent"
    ok = agent_subdir.is_dir()
    check("workspace_agent_subdir_exists",
          ok,
          f"{agent_subdir} {'exists' if ok else 'MISSING'}")
except Exception as e:
    check("workspace_agent_subdir_exists", False, str(e))

# ── CHECK 3: agents/{agentId}/agent directory exists ─────────────────────────
try:
    agents_agent_dir = AGENTS_DIR / "agent"
    ok = agents_agent_dir.is_dir()
    check("agents_dir_exists",
          ok,
          f"{agents_agent_dir} {'exists' if ok else 'MISSING'}")
except Exception as e:
    check("agents_dir_exists", False, str(e))

# ── CHECK 4-8: All five template files present in workspace ──────────────────
REQUIRED_TEMPLATES = ["IDENTITY.md", "SOUL.md", "USER.md", "AGENTS.md", "MEMORY.md"]
for fname in REQUIRED_TEMPLATES:
    try:
        fpath = WORKSPACE / fname
        ok = fpath.is_file()
        # Also check content is non-empty and matches template content
        detail = f"{fpath} {'exists' if ok else 'MISSING'}"
        if ok:
            content = fpath.read_text()
            template_content = (TEMPLATES_DIR / fname).read_text()
            if content.strip() == template_content.strip():
                detail += " (content matches template ✓)"
            elif len(content.strip()) > 0:
                detail += " (content differs from template but non-empty — acceptable)"
            else:
                ok = False
                detail += " (file is empty!)"
        check(f"template_file_{fname.lower().replace('.','_')}", ok, detail)
    except Exception as e:
        check(f"template_file_{fname.lower().replace('.','_')}", False, str(e))

# ── CHECK 9: agent/models.json exists and has correct provider ────────────────
try:
    models_path = WORKSPACE / "agent" / "models.json"
    ok = models_path.is_file()
    if ok:
        models = json.loads(models_path.read_text())
        primary = models.get("primary", {})
        # Accept either nested {provider, modelId} or flat string reference
        provider_ok = False
        modelid_ok = False
        if isinstance(primary, dict):
            provider_ok = primary.get("provider", "").lower() == PROVIDER.lower()
            modelid_ok = primary.get("modelId", "").lower() == MODEL_ID.lower()
            detail = (f"provider={primary.get('provider')} (expected {PROVIDER}), "
                      f"modelId={primary.get('modelId')} (expected {MODEL_ID})")
        else:
            detail = f"primary is not a dict: {primary}"
        passed = ok and provider_ok and modelid_ok
        check("models_json_correct_provider", passed, detail)
    else:
        check("models_json_correct_provider", False, f"{models_path} MISSING")
except Exception as e:
    check("models_json_correct_provider", False, str(e))

# ── CHECK 10: agent/auth.json exists ─────────────────────────────────────────
try:
    auth_path = WORKSPACE / "agent" / "auth.json"
    ok = auth_path.is_file()
    if ok:
        auth = json.loads(auth_path.read_text())
        # Must be a dict (empty {} is fine per SKILL.md)
        is_dict = isinstance(auth, dict)
        check("auth_json_exists_valid",
              is_dict,
              f"auth.json {'is valid dict' if is_dict else 'is not a dict: ' + str(auth)}")
    else:
        check("auth_json_exists_valid", False, f"{auth_path} MISSING")
except Exception as e:
    check("auth_json_exists_valid", False, str(e))

# ── CHECK 11: openclaw.json — agents.list updated ─────────────────────────────
try:
    cfg_path = OPENCLAW / "openclaw.json"
    cfg = json.loads(cfg_path.read_text())
    agent_list = cfg.get("agents", {}).get("list", [])
    new_agent = next((a for a in agent_list if a.get("id") == AGENT_ID), None)
    
    if new_agent is None:
        check("openclaw_agents_list_updated", False,
              f"Agent '{AGENT_ID}' not found in agents.list")
    else:
        # Check model.primary format: "{provider}/{modelId}"
        model_primary = new_agent.get("model", {}).get("primary", "")
        primary_ok = model_primary.lower() == EXPECTED_MODEL_PRIMARY.lower()
        ws_ok = AGENT_ID in new_agent.get("workspace", "")
        passed = primary_ok and ws_ok
        detail = (f"id='{new_agent.get('id')}', "
                  f"model.primary='{model_primary}' (expected '{EXPECTED_MODEL_PRIMARY}'), "
                  f"workspace contains agentId: {ws_ok}")
        check("openclaw_agents_list_updated", passed, detail)
except Exception as e:
    check("openclaw_agents_list_updated", False, str(e))

# ── CHECK 12: openclaw.json — agentToAgent.allow updated ─────────────────────
try:
    cfg_path = OPENCLAW / "openclaw.json"
    cfg = json.loads(cfg_path.read_text())
    allow_list = cfg.get("agentToAgent", {}).get("allow", [])
    
    main_still_there = "agent-main" in allow_list
    new_added = AGENT_ID in allow_list
    passed = main_still_there and new_added
    check("openclaw_a2a_allow_updated",
          passed,
          f"allow={allow_list}, "
          f"agent-main present: {main_still_there}, "
          f"'{AGENT_ID}' present: {new_added}")
except Exception as e:
    check("openclaw_a2a_allow_updated", False, str(e))

# ── CHECK 13: openclaw.json — bindings entry added ───────────────────────────
try:
    cfg_path = OPENCLAW / "openclaw.json"
    cfg = json.loads(cfg_path.read_text())
    bindings = cfg.get("bindings", [])
    
    binding = next(
        (b for b in bindings
         if b.get("agentId") == AGENT_ID
         and b.get("match", {}).get("channel") == "feishu"
         and b.get("match", {}).get("accountId") == FEISHU_ACCOUNT_ID),
        None
    )
    passed = binding is not None
    check("openclaw_bindings_feishu_added",
          passed,
          f"Found feishu binding for {AGENT_ID}/{FEISHU_ACCOUNT_ID}: {passed}. "
          f"All bindings: {json.dumps(bindings)}")
except Exception as e:
    check("openclaw_bindings_feishu_added", False, str(e))

# ── CHECK 14: openclaw.json — channels.accounts entry added ──────────────────
try:
    cfg_path = OPENCLAW / "openclaw.json"
    cfg = json.loads(cfg_path.read_text())
    accounts = cfg.get("channels", {}).get("accounts", {})
    
    account = accounts.get(FEISHU_ACCOUNT_ID)
    if account is None:
        check("openclaw_channels_accounts_feishu",
              False,
              f"No entry for accountId='{FEISHU_ACCOUNT_ID}' in channels.accounts. "
              f"Keys present: {list(accounts.keys())}")
    else:
        appid_ok = account.get("appId") == FEISHU_APP_ID
        secret_ok = account.get("appSecret") == FEISHU_APP_SECRET
        botname_ok = account.get("botName") == FEISHU_BOT_NAME
        passed = appid_ok and secret_ok and botname_ok
        check("openclaw_channels_accounts_feishu",
              passed,
              f"appId={account.get('appId')} (expected {FEISHU_APP_ID}): {appid_ok}, "
              f"appSecret={'ok' if secret_ok else 'WRONG'}, "
              f"botName={account.get('botName')} (expected {FEISHU_BOT_NAME}): {botname_ok}")
except Exception as e:
    check("openclaw_channels_accounts_feishu", False, str(e))

# ── CHECK 15: Integrity — original agent-main still intact ────────────────────
try:
    cfg_path = OPENCLAW / "openclaw.json"
    cfg = json.loads(cfg_path.read_text())
    agent_list = cfg.get("agents", {}).get("list", [])
    main_agent = next((a for a in agent_list if a.get("id") == "agent-main"), None)
    ok = main_agent is not None
    check("original_agent_main_preserved",
          ok,
          f"agent-main in agents.list: {ok}")
except Exception as e:
    check("original_agent_main_preserved", False, str(e))

# ── SCORE ─────────────────────────────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 4)
all_passed = passed_count == total

result = {
    "passed": all_passed,
    "score": score,
    "checks": checks
}

print(json.dumps(result, indent=2))
sys.exit(0 if all_passed else 1)