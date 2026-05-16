import sys
import json
import os
from pathlib import Path

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    base = Path(workspace)
    config_path = base / "config" / "openclaw.json"
    
    checks = []
    total_score = 0.0
    weights = {
        "config_readable": 0.05,
        "bot_deprecated_q2_deleted": 0.20,
        "bot_hr_chatbot_added": 0.15,
        "bot_hr_chatbot_appid_correct": 0.05,
        "bot_hr_chatbot_secret_correct": 0.05,
        "bot_hr_chatbot_model_default": 0.10,
        "bot_devops_helper_added": 0.10,
        "bot_devops_helper_model_correct": 0.05,
        "bot_sales_updated_secret": 0.10,
        "bot_sales_updated_model": 0.05,
        "backup_created": 0.05,
        "gateway_restarted": 0.05,
    }

    # --- Read config ---
    config = None
    try:
        config = json.loads(config_path.read_text())
        checks.append(check("config_readable", True, "openclaw.json is valid JSON"))
        total_score += weights["config_readable"]
    except Exception as e:
        checks.append(check("config_readable", False, f"Cannot read openclaw.json: {e}"))
        # Cannot continue without config
        result = {
            "passed": False,
            "score": 0.0,
            "checks": checks + [
                check(k, False, "Config unreadable, skipped") for k in weights if k != "config_readable"
            ]
        }
        print(json.dumps(result))
        return

    bots = {b["botId"]: b for b in config.get("bots", [])}

    # --- Check 1: bot-deprecated-q2 deleted ---
    deleted = "bot-deprecated-q2" not in bots
    checks.append(check(
        "bot_deprecated_q2_deleted",
        deleted,
        "bot-deprecated-q2 is absent from config" if deleted else "bot-deprecated-q2 still present (should be deleted)"
    ))
    if deleted:
        total_score += weights["bot_deprecated_q2_deleted"]

    # --- Check 2: bot-hr-chatbot added ---
    hr_bot = bots.get("bot-hr-chatbot")
    hr_present = hr_bot is not None
    checks.append(check(
        "bot_hr_chatbot_added",
        hr_present,
        "bot-hr-chatbot found in config" if hr_present else "bot-hr-chatbot NOT found in config"
    ))
    if hr_present:
        total_score += weights["bot_hr_chatbot_added"]

    # --- Check 3: bot-hr-chatbot appId ---
    if hr_bot:
        app_id_ok = hr_bot.get("appId") == "cli_hr_20240701"
        checks.append(check(
            "bot_hr_chatbot_appid_correct",
            app_id_ok,
            f"appId={hr_bot.get('appId')} (expected cli_hr_20240701)"
        ))
        if app_id_ok:
            total_score += weights["bot_hr_chatbot_appid_correct"]
    else:
        checks.append(check("bot_hr_chatbot_appid_correct", False, "bot-hr-chatbot absent"))

    # --- Check 4: bot-hr-chatbot appSecret ---
    if hr_bot:
        secret_ok = hr_bot.get("appSecret") == "HR_SECRET_Q3_2024"
        checks.append(check(
            "bot_hr_chatbot_secret_correct",
            secret_ok,
            f"appSecret={'[correct]' if secret_ok else hr_bot.get('appSecret')} (expected HR_SECRET_Q3_2024)"
        ))
        if secret_ok:
            total_score += weights["bot_hr_chatbot_secret_correct"]
    else:
        checks.append(check("bot_hr_chatbot_secret_correct", False, "bot-hr-chatbot absent"))

    # --- Check 5: bot-hr-chatbot uses default model (no --model specified) ---
    if hr_bot:
        # Default model per SKILL.md is "bailian-coding-plan/glm-5"
        model_default = hr_bot.get("model") == "bailian-coding-plan/glm-5"
        checks.append(check(
            "bot_hr_chatbot_model_default",
            model_default,
            f"model={hr_bot.get('model')} (expected default: bailian-coding-plan/glm-5)"
        ))
        if model_default:
            total_score += weights["bot_hr_chatbot_model_default"]
    else:
        checks.append(check("bot_hr_chatbot_model_default", False, "bot-hr-chatbot absent"))

    # --- Check 6: bot-devops-helper added ---
    devops_bot = bots.get("bot-devops-helper")
    devops_present = devops_bot is not None
    checks.append(check(
        "bot_devops_helper_added",
        devops_present,
        "bot-devops-helper found in config" if devops_present else "bot-devops-helper NOT found in config"
    ))
    if devops_present:
        total_score += weights["bot_devops_helper_added"]

    # --- Check 7: bot-devops-helper model is glm-4-flash ---
    if devops_bot:
        devops_model_ok = devops_bot.get("model") == "glm-4-flash"
        checks.append(check(
            "bot_devops_helper_model_correct",
            devops_model_ok,
            f"model={devops_bot.get('model')} (expected glm-4-flash)"
        ))
        if devops_model_ok:
            total_score += weights["bot_devops_helper_model_correct"]
    else:
        checks.append(check("bot_devops_helper_model_correct", False, "bot-devops-helper absent"))

    # --- Check 8: bot-sales-assistant appSecret updated ---
    sales_bot = bots.get("bot-sales-assistant")
    if sales_bot:
        sales_secret_ok = sales_bot.get("appSecret") == "SECRET_SALES_NEWKEY_2024"
        checks.append(check(
            "bot_sales_updated_secret",
            sales_secret_ok,
            f"appSecret={'[correct]' if sales_secret_ok else sales_bot.get('appSecret')} (expected SECRET_SALES_NEWKEY_2024)"
        ))
        if sales_secret_ok:
            total_score += weights["bot_sales_updated_secret"]
    else:
        checks.append(check("bot_sales_updated_secret", False, "bot-sales-assistant not found"))

    # --- Check 9: bot-sales-assistant model updated ---
    if sales_bot:
        sales_model_ok = sales_bot.get("model") == "qwen-max"
        checks.append(check(
            "bot_sales_updated_model",
            sales_model_ok,
            f"model={sales_bot.get('model')} (expected qwen-max)"
        ))
        if sales_model_ok:
            total_score += weights["bot_sales_updated_model"]
    else:
        checks.append(check("bot_sales_updated_model", False, "bot-sales-assistant not found"))

    # --- Check 10: Backup file created ---
    backup_dir = base / "config"
    backups = list(backup_dir.glob("openclaw.json.bak.*"))
    # Validate backup filename format: openclaw.json.bak.YYYY.MMdd.HHmm
    import re
    valid_backups = [b for b in backups if re.match(r"openclaw\.json\.bak\.\d{4}\.\d{4}\.\d{4}$", b.name)]
    backup_ok = len(valid_backups) >= 1
    checks.append(check(
        "backup_created",
        backup_ok,
        f"Found {len(valid_backups)} valid backup(s): {[b.name for b in valid_backups]}" if backup_ok
        else f"No valid backup found. Files: {[b.name for b in backups]}"
    ))
    if backup_ok:
        total_score += weights["backup_created"]

    # --- Check 11: Gateway restart was called ---
    restart_marker = base / "logs" / "gateway" / "restart_called"
    try:
        if restart_marker.exists():
            content = restart_marker.read_text()
            restarted = "restarted" in content.lower() or len(content.strip()) > 0
        else:
            restarted = False
        checks.append(check(
            "gateway_restarted",
            restarted,
            "openclaw gateway restart was called" if restarted else "No evidence of gateway restart"
        ))
        if restarted:
            total_score += weights["gateway_restarted"]
    except Exception as e:
        checks.append(check("gateway_restarted", False, f"Error checking restart: {e}"))

    # Final
    total_score = round(total_score, 4)
    passed = total_score >= 0.75 and all(c["passed"] for c in checks if c["name"] in [
        "config_readable", "bot_deprecated_q2_deleted", "bot_hr_chatbot_added",
        "bot_devops_helper_added", "bot_sales_updated_secret"
    ])

    result = {
        "passed": passed,
        "score": total_score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()