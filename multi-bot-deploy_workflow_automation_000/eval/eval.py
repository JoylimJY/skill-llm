#!/usr/bin/env python3
"""
Evaluation script for multi-bot-deploy task.
Checks that the agent correctly ran the full 5-step openclaw workflow
for BOTH bots derived from the business request.
"""
import sys
import json
import re
import os
from pathlib import Path

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def load_lines(path):
    with open(path, "r") as f:
        return [line.strip() for line in f.readlines() if line.strip()]

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    checks = []
    
    LOG_FILE = "/root/.openclaw/command_log.txt"
    CONFIG_FILE = "/root/.openclaw/openclaw.json"
    OPENCLAW_DIR = "/root/.openclaw"

    # Expected derived values from the business request:
    # Bot 1: "Aria-HR" → agentId: "aria-hr", workspace: "/root/.openclaw/workspace-aria-hr"
    # Bot 2: "CodeReview-Pro" → agentId: "codereview-pro" OR "code-review-pro" acceptable
    #         workspace: "/root/.openclaw/workspace-codereview-pro" (matching agentId)
    # We'll be flexible on exact agentId for Bot2 but strict on consistency

    # ── Load command log ───────────────────────────────────────────────────────
    try:
        log_lines = load_lines(LOG_FILE)
        cmd_log = "\n".join(log_lines)
    except Exception as e:
        checks.append({"name": "command_log_readable", "passed": False,
                        "detail": f"Cannot read command log: {e}"})
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result))
        return

    checks.append({"name": "command_log_readable", "passed": True,
                    "detail": f"Command log has {len(log_lines)} entries"})

    # ── Load final config ──────────────────────────────────────────────────────
    try:
        config = load_json(CONFIG_FILE)
    except Exception as e:
        config = {}
        checks.append({"name": "config_readable", "passed": False,
                        "detail": f"Cannot read config: {e}"})
    else:
        checks.append({"name": "config_readable", "passed": True, "detail": "Config JSON is valid"})

    # ── CHECK 1: Backup was created ────────────────────────────────────────────
    try:
        backups = list(Path(OPENCLAW_DIR).glob("openclaw.json.bak_*"))
        backup_passed = len(backups) > 0
        checks.append({
            "name": "backup_created",
            "passed": backup_passed,
            "detail": f"Backup files found: {[b.name for b in backups]}" if backup_passed
                      else "No backup file matching openclaw.json.bak_* found"
        })
    except Exception as e:
        checks.append({"name": "backup_created", "passed": False, "detail": str(e)})

    # ── CHECK 2: Bot 1 (Aria-HR) agent created with correct agentId ───────────
    # agentId must be lowercase + hyphen → "aria-hr"
    try:
        agents = config.get("agents", {})
        bot1_id = "aria-hr"
        bot1_present = bot1_id in agents
        checks.append({
            "name": "bot1_agent_created",
            "passed": bot1_present,
            "detail": f"Agent 'aria-hr' in config: {bot1_present}. Existing agents: {list(agents.keys())}"
        })
    except Exception as e:
        bot1_present = False
        checks.append({"name": "bot1_agent_created", "passed": False, "detail": str(e)})

    # ── CHECK 3: Bot 1 workspace path is correct ───────────────────────────────
    try:
        bot1_workspace = config.get("agents", {}).get("aria-hr", {}).get("workspace", "")
        expected_ws1 = "/root/.openclaw/workspace-aria-hr"
        ws1_correct = bot1_workspace == expected_ws1
        checks.append({
            "name": "bot1_workspace_path",
            "passed": ws1_correct,
            "detail": f"Bot1 workspace: '{bot1_workspace}', expected: '{expected_ws1}'"
        })
    except Exception as e:
        ws1_correct = False
        checks.append({"name": "bot1_workspace_path", "passed": False, "detail": str(e)})

    # ── CHECK 4: Bot 1 model is correct ───────────────────────────────────────
    try:
        bot1_model = config.get("agents", {}).get("aria-hr", {}).get("model", "")
        expected_model1 = "bailian/qwen3.5-plus"
        model1_correct = bot1_model == expected_model1
        checks.append({
            "name": "bot1_model_correct",
            "passed": model1_correct,
            "detail": f"Bot1 model: '{bot1_model}', expected: '{expected_model1}'"
        })
    except Exception as e:
        model1_correct = False
        checks.append({"name": "bot1_model_correct", "passed": False, "detail": str(e)})

    # ── CHECK 5: Bot 2 (CodeReview-Pro) agent created ─────────────────────────
    # Accept "codereview-pro" or "code-review-pro" but must be all-lowercase+hyphen
    try:
        agents = config.get("agents", {})
        bot2_candidates = [k for k in agents if re.match(r'^code[-]?review[-]pro$', k)]
        bot2_id = bot2_candidates[0] if bot2_candidates else None
        bot2_present = bot2_id is not None
        checks.append({
            "name": "bot2_agent_created",
            "passed": bot2_present,
            "detail": f"Bot2 agent found: '{bot2_id}'. All agents: {list(agents.keys())}"
        })
    except Exception as e:
        bot2_present = False
        bot2_id = None
        checks.append({"name": "bot2_agent_created", "passed": False, "detail": str(e)})

    # ── CHECK 6: Bot 2 uses correct coder model ────────────────────────────────
    try:
        expected_model2 = "bailian/qwen3-coder-plus"
        if bot2_id:
            bot2_model = config.get("agents", {}).get(bot2_id, {}).get("model", "")
            model2_correct = bot2_model == expected_model2
        else:
            bot2_model = ""
            model2_correct = False
        checks.append({
            "name": "bot2_model_correct",
            "passed": model2_correct,
            "detail": f"Bot2 model: '{bot2_model}', expected: '{expected_model2}'"
        })
    except Exception as e:
        model2_correct = False
        checks.append({"name": "bot2_model_correct", "passed": False, "detail": str(e)})

    # ── CHECK 7: Bot 2 workspace path consistent with its agentId ─────────────
    try:
        if bot2_id:
            bot2_workspace = config.get("agents", {}).get(bot2_id, {}).get("workspace", "")
            expected_ws2 = f"/root/.openclaw/workspace-{bot2_id}"
            ws2_correct = bot2_workspace == expected_ws2
        else:
            bot2_workspace = ""
            expected_ws2 = "/root/.openclaw/workspace-<bot2-id>"
            ws2_correct = False
        checks.append({
            "name": "bot2_workspace_path",
            "passed": ws2_correct,
            "detail": f"Bot2 workspace: '{bot2_workspace}', expected: '{expected_ws2}'"
        })
    except Exception as e:
        ws2_correct = False
        checks.append({"name": "bot2_workspace_path", "passed": False, "detail": str(e)})

    # ── CHECK 8: Bot 1 feishu account credentials set correctly ───────────────
    try:
        feishu_accounts = config.get("channels", {}).get("feishu", {}).get("accounts", {})
        bot1_feishu = feishu_accounts.get("aria-hr", {})
        app_id_ok = bot1_feishu.get("appId", "") == "cli_a1b2c3d4e5f6g7h8"
        app_secret_ok = bot1_feishu.get("appSecret", "") == "HRSecretKey2025XYZ99"
        creds1_ok = app_id_ok and app_secret_ok
        checks.append({
            "name": "bot1_feishu_credentials",
            "passed": creds1_ok,
            "detail": f"Bot1 appId correct: {app_id_ok}, appSecret correct: {app_secret_ok}. "
                      f"Found account keys: {list(bot1_feishu.keys())}"
        })
    except Exception as e:
        creds1_ok = False
        checks.append({"name": "bot1_feishu_credentials", "passed": False, "detail": str(e)})

    # ── CHECK 9: Bot 2 feishu account credentials set correctly ───────────────
    try:
        feishu_accounts = config.get("channels", {}).get("feishu", {}).get("accounts", {})
        bot2_feishu = feishu_accounts.get(bot2_id, {}) if bot2_id else {}
        app_id2_ok = bot2_feishu.get("appId", "") == "cli_z9y8x7w6v5u4t3s2"
        app_secret2_ok = bot2_feishu.get("appSecret", "") == "CodeSecretKey2025ABC88"
        creds2_ok = app_id2_ok and app_secret2_ok
        checks.append({
            "name": "bot2_feishu_credentials",
            "passed": creds2_ok,
            "detail": f"Bot2 appId correct: {app_id2_ok}, appSecret correct: {app_secret2_ok}. "
                      f"Found account data: {bot2_feishu}"
        })
    except Exception as e:
        creds2_ok = False
        checks.append({"name": "bot2_feishu_credentials", "passed": False, "detail": str(e)})

    # ── CHECK 10: Config set commands used dotted key format ──────────────────
    try:
        # Check that config set was called with the exact nested key format
        config_set_lines = [l for l in log_lines if "openclaw config set" in l]
        # Must include keys like: channels.feishu.accounts.aria-hr.appId
        bot1_appid_set = any("channels.feishu.accounts.aria-hr.appId" in l for l in config_set_lines)
        bot1_secret_set = any("channels.feishu.accounts.aria-hr.appSecret" in l for l in config_set_lines)
        config_key_format_ok = bot1_appid_set and bot1_secret_set
        checks.append({
            "name": "config_set_key_format",
            "passed": config_key_format_ok,
            "detail": f"Bot1 appId key used: {bot1_appid_set}, appSecret key used: {bot1_secret_set}. "
                      f"Config set commands found: {len(config_set_lines)}"
        })
    except Exception as e:
        config_key_format_ok = False
        checks.append({"name": "config_set_key_format", "passed": False, "detail": str(e)})

    # ── CHECK 11: Route bindings correct for both bots ────────────────────────
    try:
        bindings = config.get("bindings", [])
        # Bot 1 binding must be: "feishu:aria-hr -> aria-hr"
        bot1_binding_ok = any("feishu:aria-hr" in b and "aria-hr" in b for b in bindings)
        # Bot 2 binding must match its agentId
        bot2_binding_ok = False
        if bot2_id:
            bot2_binding_ok = any(f"feishu:{bot2_id}" in b and bot2_id in b for b in bindings)
        checks.append({
            "name": "route_bindings_correct",
            "passed": bot1_binding_ok and bot2_binding_ok,
            "detail": f"Bot1 binding ok: {bot1_binding_ok}, Bot2 binding ok: {bot2_binding_ok}. "
                      f"All bindings: {bindings}"
        })
    except Exception as e:
        checks.append({"name": "route_bindings_correct", "passed": False, "detail": str(e)})

    # ── CHECK 12: Gateway restart was called ──────────────────────────────────
    try:
        restart_calls = [l for l in log_lines if "openclaw gateway restart" in l]
        # Should be called at least once (ideally after each bot or at the end)
        gateway_restarted = len(restart_calls) >= 1
        checks.append({
            "name": "gateway_restarted",
            "passed": gateway_restarted,
            "detail": f"Gateway restart calls: {len(restart_calls)}"
        })
    except Exception as e:
        checks.append({"name": "gateway_restarted", "passed": False, "detail": str(e)})

    # ── CHECK 13: agents list and config get bindings were run (verification) ─
    try:
        agents_list_ok = any("openclaw agents list" in l for l in log_lines)
        config_get_ok = any("openclaw config get bindings" in l for l in log_lines)
        verification_ok = agents_list_ok and config_get_ok
        checks.append({
            "name": "verification_steps_run",
            "passed": verification_ok,
            "detail": f"agents list run: {agents_list_ok}, config get bindings run: {config_get_ok}"
        })
    except Exception as e:
        checks.append({"name": "verification_steps_run", "passed": False, "detail": str(e)})

    # ── CHECK 14: --non-interactive flag used for agent creation ──────────────
    try:
        add_cmds = [l for l in log_lines if "openclaw agents add" in l]
        non_interactive_uses = [l for l in add_cmds if "--non-interactive" in l]
        # Both bots should use --non-interactive
        ni_ok = len(non_interactive_uses) >= 2
        checks.append({
            "name": "non_interactive_flag_used",
            "passed": ni_ok,
            "detail": f"agents add commands: {len(add_cmds)}, with --non-interactive: {len(non_interactive_uses)}"
        })
    except Exception as e:
        checks.append({"name": "non_interactive_flag_used", "passed": False, "detail": str(e)})

    # ── Scoring ────────────────────────────────────────────────────────────────
    # Weight critical checks more heavily
    critical_checks = [
        "bot1_agent_created", "bot1_workspace_path", "bot1_model_correct",
        "bot2_agent_created", "bot2_model_correct", "bot2_workspace_path",
        "bot1_feishu_credentials", "bot2_feishu_credentials",
        "route_bindings_correct", "backup_created"
    ]
    regular_checks = [
        "config_set_key_format", "gateway_restarted",
        "verification_steps_run", "non_interactive_flag_used"
    ]

    check_map = {c["name"]: c["passed"] for c in checks}

    critical_score = sum(1 for c in critical_checks if check_map.get(c, False))
    regular_score = sum(1 for c in regular_checks if check_map.get(c, False))

    total_score = (critical_score / len(critical_checks)) * 0.75 + \
                  (regular_score / len(regular_checks)) * 0.25

    all_critical_pass = all(check_map.get(c, False) for c in critical_checks)
    overall_passed = all_critical_pass and total_score >= 0.80

    result = {
        "passed": overall_passed,
        "score": round(total_score, 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()