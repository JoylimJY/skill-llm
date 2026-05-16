import json
import os
import sys

def evaluate(workspace_dir):
    checks = []
    config_path = os.path.join(os.path.expanduser("~"), ".openclaw", "openclaw.json")

    # --- Load config file ---
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except FileNotFoundError:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "config_file_exists", "passed": False, "detail": f"Config file not found at {config_path}"}]
        }
    except json.JSONDecodeError as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "config_file_valid_json", "passed": False, "detail": f"Config file is invalid JSON: {e}"}]
        }

    # --- Check 1: Original sales agent preserved ---
    try:
        agents_list = config["agents"]["list"]
        sales_agent = next((a for a in agents_list if a.get("id") == "sales"), None)
        passed = sales_agent is not None and sales_agent.get("default") == True
        checks.append({
            "name": "original_sales_agent_preserved",
            "passed": passed,
            "detail": "Original 'sales' agent with default:true must remain intact." if not passed else "OK"
        })
    except Exception as e:
        checks.append({"name": "original_sales_agent_preserved", "passed": False, "detail": str(e)})

    # --- Check 2: New HR agent exists in agents.list ---
    try:
        agents_list = config["agents"]["list"]
        hr_agent = next((a for a in agents_list if a.get("id") == "hr-support"), None)
        passed = hr_agent is not None
        checks.append({
            "name": "hr_agent_exists_in_list",
            "passed": passed,
            "detail": "Agent with id='hr-support' must exist in agents.list." if not passed else "OK"
        })
    except Exception as e:
        checks.append({"name": "hr_agent_exists_in_list", "passed": False, "detail": str(e)})
        hr_agent = None

    # --- Check 3: HR agent has correct required fields ---
    try:
        assert hr_agent is not None, "hr_agent not found"
        has_name = isinstance(hr_agent.get("name"), str) and len(hr_agent["name"]) > 0
        has_workspace = isinstance(hr_agent.get("workspace"), str) and "workspace" in hr_agent["workspace"]
        has_model_primary = (
            isinstance(hr_agent.get("model"), dict) and
            hr_agent["model"].get("primary") == "ark/doubao"
        )
        passed = has_name and has_workspace and has_model_primary
        checks.append({
            "name": "hr_agent_correct_structure",
            "passed": passed,
            "detail": (
                f"HR agent must have: name(str)={has_name}, workspace(str with 'workspace')={has_workspace}, "
                f"model.primary='ark/doubao'={has_model_primary}"
            ) if not passed else "OK"
        })
    except Exception as e:
        checks.append({"name": "hr_agent_correct_structure", "passed": False, "detail": str(e)})

    # --- Check 4: New Feishu account added under channels.feishu.accounts ---
    try:
        feishu_accounts = config["channels"]["feishu"]["accounts"]
        # Find any account that is NOT "sales-bot" (new account for hr)
        new_accounts = {k: v for k, v in feishu_accounts.items() if k != "sales-bot"}
        passed = len(new_accounts) >= 1
        hr_account_id = list(new_accounts.keys())[0] if new_accounts else None
        hr_account = new_accounts.get(hr_account_id) if hr_account_id else None
        checks.append({
            "name": "new_feishu_account_added",
            "passed": passed,
            "detail": "A new account (non 'sales-bot') must exist under channels.feishu.accounts." if not passed else f"Found new account: '{hr_account_id}'"
        })
    except Exception as e:
        checks.append({"name": "new_feishu_account_added", "passed": False, "detail": str(e)})
        hr_account = None
        hr_account_id = None

    # --- Check 5: New Feishu account has required fields including dmPolicy and allowFrom ---
    try:
        assert hr_account is not None, "hr_account not found"
        has_appId = isinstance(hr_account.get("appId"), str) and hr_account["appId"].startswith("cli_")
        has_appSecret = isinstance(hr_account.get("appSecret"), str) and len(hr_account["appSecret"]) > 0
        has_botName = isinstance(hr_account.get("botName"), str) and len(hr_account["botName"]) > 0
        dm_policy = hr_account.get("dmPolicy")
        has_valid_dmPolicy = dm_policy in ("allowlist", "open", "denylist")
        has_allowFrom = isinstance(hr_account.get("allowFrom"), list)
        # If dmPolicy is allowlist, allowFrom must be non-empty
        if dm_policy == "allowlist":
            has_allowFrom = has_allowFrom and len(hr_account["allowFrom"]) > 0
        passed = has_appId and has_appSecret and has_botName and has_valid_dmPolicy and has_allowFrom
        checks.append({
            "name": "new_feishu_account_correct_fields",
            "passed": passed,
            "detail": (
                f"appId(cli_ prefix)={has_appId}, appSecret={has_appSecret}, botName={has_botName}, "
                f"dmPolicy(valid)={has_valid_dmPolicy}(got '{dm_policy}'), allowFrom(list, non-empty if allowlist)={has_allowFrom}"
            ) if not passed else "OK"
        })
    except Exception as e:
        checks.append({"name": "new_feishu_account_correct_fields", "passed": False, "detail": str(e)})

    # --- Check 6: New binding exists linking hr-support agent to new feishu account ---
    try:
        bindings = config.get("bindings", [])
        hr_binding = next(
            (b for b in bindings
             if b.get("agentId") == "hr-support" and
                isinstance(b.get("match"), dict) and
                b["match"].get("channel") == "feishu" and
                b["match"].get("accountId") == hr_account_id),
            None
        )
        passed = hr_binding is not None
        checks.append({
            "name": "hr_binding_exists",
            "passed": passed,
            "detail": (
                f"A binding with agentId='hr-support', match.channel='feishu', "
                f"match.accountId='{hr_account_id}' must exist in bindings."
            ) if not passed else "OK"
        })
    except Exception as e:
        checks.append({"name": "hr_binding_exists", "passed": False, "detail": str(e)})

    # --- Check 7: Original sales binding preserved ---
    try:
        bindings = config.get("bindings", [])
        sales_binding = next(
            (b for b in bindings
             if b.get("agentId") == "sales" and
                isinstance(b.get("match"), dict) and
                b["match"].get("channel") == "feishu" and
                b["match"].get("accountId") == "sales-bot"),
            None
        )
        passed = sales_binding is not None
        checks.append({
            "name": "original_sales_binding_preserved",
            "passed": passed,
            "detail": "Original sales binding must not be removed." if not passed else "OK"
        })
    except Exception as e:
        checks.append({"name": "original_sales_binding_preserved", "passed": False, "detail": str(e)})

    # --- Check 8: HR workspace directory created ---
    try:
        if hr_agent and hr_agent.get("workspace"):
            ws_path = hr_agent["workspace"].replace("~", os.path.expanduser("~"))
            passed = os.path.isdir(ws_path)
            checks.append({
                "name": "hr_workspace_directory_created",
                "passed": passed,
                "detail": f"Workspace directory '{ws_path}' must exist on disk." if not passed else f"OK: {ws_path}"
            })
        else:
            checks.append({
                "name": "hr_workspace_directory_created",
                "passed": False,
                "detail": "Cannot check workspace dir: hr_agent or workspace field missing."
            })
    except Exception as e:
        checks.append({"name": "hr_workspace_directory_created", "passed": False, "detail": str(e)})

    # --- Check 9: dmPolicy uses allowlist (not open) — HR requires restricted access ---
    try:
        assert hr_account is not None, "hr_account not found"
        dm_policy = hr_account.get("dmPolicy")
        passed = dm_policy == "allowlist"
        checks.append({
            "name": "hr_account_uses_allowlist_policy",
            "passed": passed,
            "detail": f"HR bot must use dmPolicy='allowlist' for restricted access, got '{dm_policy}'." if not passed else "OK"
        })
    except Exception as e:
        checks.append({"name": "hr_account_uses_allowlist_policy", "passed": False, "detail": str(e)})

    # --- Scoring ---
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
    workspace = sys.argv[1] if len(sys.argv) > 1 else "."
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))