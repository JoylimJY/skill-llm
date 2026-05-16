#!/usr/bin/env python3
"""
Evaluation script for the OpenClaw agent creator task.

Expected final state:
  - Agent 'tuikuan' (退款助手) created with appId=cli_tuikuan001, appSecret=secret_tuikuan, model=deepseek-v3, description="退款专员，处理订单退款问题"
  - Agent 'dingdan' (订单助手) created with appId=cli_dingdan002, appSecret=secret_dingdan (default model glm-5), description="订单查询助手"
  - Agent 'testbot' (测试机器人) created then DELETED
  - Agent 'main' still exists (NOT deleted)
  - openclaw gateway restart was called at least once
  - Directory structure correct for surviving agents
"""

import sys
import json
import os
from pathlib import Path

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def run_eval(workspace):
    checks = []
    total_score = 0.0

    CONFIG_PATH = "/home/admin/.openclaw/openclaw.json"
    AGENTS_DIR = "/home/admin/.openclaw/agents"
    OPENCLAW_DIR = "/home/admin/.openclaw"

    # ── Check 1: Config file is valid JSON ────────────────────────────────────
    try:
        config = load_json(CONFIG_PATH)
        checks.append({"name": "config_valid_json", "passed": True, "detail": "openclaw.json is valid JSON"})
    except Exception as e:
        checks.append({"name": "config_valid_json", "passed": False, "detail": f"Failed to load openclaw.json: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── Check 2: main agent NOT deleted ──────────────────────────────────────
    try:
        main_in_list = "main" in config["agents"]["list"]
        main_has_binding = any(b.get("agent") == "main" for b in config.get("bindings", []))
        main_in_a2a = "main" in config.get("tools", {}).get("agentToAgent", {}).get("allow", [])
        main_ok = main_in_list and main_has_binding and main_in_a2a
        checks.append({
            "name": "main_agent_preserved",
            "passed": main_ok,
            "detail": f"main in list={main_in_list}, binding={main_has_binding}, a2a={main_in_a2a}"
        })
        if main_ok:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "main_agent_preserved", "passed": False, "detail": str(e)})

    # ── Check 3: 'tuikuan' agent created with correct params ─────────────────
    try:
        tuikuan_in_list = "tuikuan" in config["agents"]["list"]
        tuikuan_feishu = config["channels"]["feishu"]["accounts"].get("tuikuan", {})
        tuikuan_app_id_ok = tuikuan_feishu.get("appId") == "cli_tuikuan001"
        tuikuan_secret_ok = tuikuan_feishu.get("appSecret") == "secret_tuikuan"
        tuikuan_binding = any(
            b.get("channel") == "feishu" and b.get("account") == "tuikuan" and b.get("agent") == "tuikuan"
            for b in config.get("bindings", [])
        )
        tuikuan_a2a = "tuikuan" in config.get("tools", {}).get("agentToAgent", {}).get("allow", [])

        # Check agent config file for model
        tuikuan_cfg_path = f"{AGENTS_DIR}/tuikuan/agent/config.json"
        try:
            tuikuan_cfg = load_json(tuikuan_cfg_path)
            tuikuan_model_ok = tuikuan_cfg.get("model") == "deepseek-v3"
            tuikuan_desc_ok = "退款" in tuikuan_cfg.get("description", "")
        except Exception:
            tuikuan_model_ok = False
            tuikuan_desc_ok = False

        tuikuan_ok = all([tuikuan_in_list, tuikuan_app_id_ok, tuikuan_secret_ok,
                          tuikuan_binding, tuikuan_a2a, tuikuan_model_ok])
        checks.append({
            "name": "tuikuan_agent_created_correctly",
            "passed": tuikuan_ok,
            "detail": (
                f"in_list={tuikuan_in_list}, appId_ok={tuikuan_app_id_ok}, "
                f"secret_ok={tuikuan_secret_ok}, binding={tuikuan_binding}, "
                f"a2a={tuikuan_a2a}, model=deepseek-v3:{tuikuan_model_ok}, desc={tuikuan_desc_ok}"
            )
        })
        if tuikuan_ok:
            total_score += 2.0
    except Exception as e:
        checks.append({"name": "tuikuan_agent_created_correctly", "passed": False, "detail": str(e)})

    # ── Check 4: 'tuikuan' directory structure ────────────────────────────────
    try:
        agent_dir = Path(f"{AGENTS_DIR}/tuikuan/agent")
        sessions_dir = Path(f"{AGENTS_DIR}/tuikuan/sessions")
        workspace_dir = Path(f"{OPENCLAW_DIR}/workspace-tuikuan")
        models_copied = Path(f"{AGENTS_DIR}/tuikuan/models.json").exists()

        dir_ok = agent_dir.is_dir() and sessions_dir.is_dir() and workspace_dir.is_dir()
        ws_files = list(workspace_dir.iterdir()) if workspace_dir.exists() else []
        ws_has_files = len(ws_files) > 0

        struct_ok = dir_ok and models_copied
        checks.append({
            "name": "tuikuan_directory_structure",
            "passed": struct_ok,
            "detail": f"agent_dir={agent_dir.exists()}, sessions={sessions_dir.exists()}, workspace={workspace_dir.exists()}, models_copied={models_copied}, ws_files={len(ws_files)}"
        })
        if struct_ok:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "tuikuan_directory_structure", "passed": False, "detail": str(e)})

    # ── Check 5: 'dingdan' agent created with default model ───────────────────
    try:
        dingdan_in_list = "dingdan" in config["agents"]["list"]
        dingdan_feishu = config["channels"]["feishu"]["accounts"].get("dingdan", {})
        dingdan_app_id_ok = dingdan_feishu.get("appId") == "cli_dingdan002"
        dingdan_secret_ok = dingdan_feishu.get("appSecret") == "secret_dingdan"
        dingdan_binding = any(
            b.get("channel") == "feishu" and b.get("account") == "dingdan" and b.get("agent") == "dingdan"
            for b in config.get("bindings", [])
        )
        dingdan_a2a = "dingdan" in config.get("tools", {}).get("agentToAgent", {}).get("allow", [])

        # Check model — should be default glm-5
        dingdan_cfg_path = f"{AGENTS_DIR}/dingdan/agent/config.json"
        try:
            dingdan_cfg = load_json(dingdan_cfg_path)
            dingdan_model_ok = dingdan_cfg.get("model") == "glm-5"
        except Exception:
            dingdan_model_ok = False

        dingdan_ok = all([dingdan_in_list, dingdan_app_id_ok, dingdan_secret_ok,
                          dingdan_binding, dingdan_a2a, dingdan_model_ok])
        checks.append({
            "name": "dingdan_agent_created_correctly",
            "passed": dingdan_ok,
            "detail": (
                f"in_list={dingdan_in_list}, appId_ok={dingdan_app_id_ok}, "
                f"secret_ok={dingdan_secret_ok}, binding={dingdan_binding}, "
                f"a2a={dingdan_a2a}, model=glm-5:{dingdan_model_ok}"
            )
        })
        if dingdan_ok:
            total_score += 2.0
    except Exception as e:
        checks.append({"name": "dingdan_agent_created_correctly", "passed": False, "detail": str(e)})

    # ── Check 6: 'testbot' deleted (NOT in config, directories removed) ───────
    try:
        testbot_not_in_list = "testbot" not in config["agents"]["list"]
        testbot_no_feishu = "testbot" not in config["channels"]["feishu"]["accounts"]
        testbot_no_binding = not any(b.get("agent") == "testbot" for b in config.get("bindings", []))
        testbot_no_a2a = "testbot" not in config.get("tools", {}).get("agentToAgent", {}).get("allow", [])
        testbot_dir_gone = not Path(f"{AGENTS_DIR}/testbot").exists()
        testbot_ws_gone = not Path(f"{OPENCLAW_DIR}/workspace-testbot").exists()

        testbot_deleted = all([testbot_not_in_list, testbot_no_feishu,
                               testbot_no_binding, testbot_no_a2a,
                               testbot_dir_gone, testbot_ws_gone])
        checks.append({
            "name": "testbot_deleted",
            "passed": testbot_deleted,
            "detail": (
                f"not_in_list={testbot_not_in_list}, no_feishu={testbot_no_feishu}, "
                f"no_binding={testbot_no_binding}, no_a2a={testbot_no_a2a}, "
                f"dir_gone={testbot_dir_gone}, ws_gone={testbot_ws_gone}"
            )
        })
        if testbot_deleted:
            total_score += 1.5
    except Exception as e:
        checks.append({"name": "testbot_deleted", "passed": False, "detail": str(e)})

    # ── Check 7: gateway restart was called ───────────────────────────────────
    try:
        restart_count_path = f"{OPENCLAW_DIR}/.gateway_restart_count"
        with open(restart_count_path) as f:
            count = int(f.read().strip())
        gateway_restarted = count >= 1
        checks.append({
            "name": "gateway_restarted",
            "passed": gateway_restarted,
            "detail": f"Gateway restart count: {count} (need >= 1)"
        })
        if gateway_restarted:
            total_score += 1.5
    except Exception as e:
        checks.append({"name": "gateway_restarted", "passed": False, "detail": str(e)})

    # ── Check 8: Final agent list sanity (main, tuikuan, dingdan only) ─────────
    try:
        expected_agents = {"main", "tuikuan", "dingdan"}
        actual_agents = set(config["agents"]["list"])
        unexpected = actual_agents - expected_agents
        missing = expected_agents - actual_agents
        list_correct = (unexpected == set() and missing == set())
        checks.append({
            "name": "final_agent_list_correct",
            "passed": list_correct,
            "detail": f"Expected={sorted(expected_agents)}, Actual={sorted(actual_agents)}, Missing={sorted(missing)}, Unexpected={sorted(unexpected)}"
        })
        if list_correct:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "final_agent_list_correct", "passed": False, "detail": str(e)})

    max_score = 10.0
    normalized_score = round(total_score / max_score, 3)
    all_critical = all(c["passed"] for c in checks)

    return {
        "passed": all_critical,
        "score": normalized_score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/home/admin"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2, ensure_ascii=False))