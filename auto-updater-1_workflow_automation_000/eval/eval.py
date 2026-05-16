import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0
    max_score = 0.0

    # ─────────────────────────────────────────────
    # CHECK 1: cron_setup.sh exists and has correct clawdbot cron add command
    # ─────────────────────────────────────────────
    max_score += 40.0
    setup_script_candidates = list(workspace.rglob("cron_setup.sh"))
    if not setup_script_candidates:
        checks.append({
            "name": "cron_setup_sh_exists",
            "passed": False,
            "detail": "cron_setup.sh not found anywhere in workspace"
        })
    else:
        script_path = setup_script_candidates[0]
        try:
            content = script_path.read_text()
        except Exception as e:
            content = ""
            checks.append({
                "name": "cron_setup_sh_readable",
                "passed": False,
                "detail": f"Could not read cron_setup.sh: {e}"
            })

        sub_checks = []

        # Must contain 'clawdbot cron add'
        has_base_cmd = "clawdbot cron add" in content
        sub_checks.append(("has_clawdbot_cron_add", has_base_cmd, "Must contain 'clawdbot cron add'"))

        # Must have --name "Daily Auto-Update"
        has_name = bool(re.search(r'--name\s+["\']?Daily Auto-Update["\']?', content))
        sub_checks.append(("has_correct_name", has_name, '--name "Daily Auto-Update" required'))

        # Must have --cron "0 4 * * *"
        has_cron_expr = bool(re.search(r'--cron\s+["\']0 4 \* \* \*["\']', content))
        sub_checks.append(("has_correct_cron_expr", has_cron_expr, '--cron "0 4 * * *" required (daily at 4AM)'))

        # Must have --session isolated (proprietary trap #1)
        has_session_isolated = bool(re.search(r'--session\s+isolated', content))
        sub_checks.append(("has_session_isolated", has_session_isolated, '--session isolated is required (proprietary flag)'))

        # Must have --wake now (proprietary trap #2)
        has_wake_now = bool(re.search(r'--wake\s+now', content))
        sub_checks.append(("has_wake_now", has_wake_now, '--wake now is required (proprietary flag)'))

        # Must have --deliver (proprietary trap #3)
        has_deliver = "--deliver" in content
        sub_checks.append(("has_deliver_flag", has_deliver, '--deliver flag is required'))

        # Must have --message with update instructions
        has_message = bool(re.search(r'--message\s+["\']', content))
        sub_checks.append(("has_message_flag", has_message, '--message "..." flag is required'))

        # Must have --tz (timezone)
        has_tz = "--tz" in content
        sub_checks.append(("has_tz_flag", has_tz, '--tz flag is required for timezone'))

        script_sub_score = sum(1 for _, p, _ in sub_checks if p) / len(sub_checks) * 40.0
        total_score += script_sub_score

        for name, passed, detail in sub_checks:
            checks.append({"name": name, "passed": passed, "detail": detail})

    # ─────────────────────────────────────────────
    # CHECK 2: cron_disable.json exists with correct structure
    # ─────────────────────────────────────────────
    max_score += 20.0
    config_candidates = list(workspace.rglob("cron_disable.json"))
    if not config_candidates:
        checks.append({
            "name": "cron_disable_json_exists",
            "passed": False,
            "detail": "cron_disable.json not found anywhere in workspace"
        })
    else:
        config_path = config_candidates[0]
        try:
            raw = config_path.read_text()
            data = json.loads(raw)

            # Must be exactly {"cron": {"enabled": false}}
            correct_structure = (
                isinstance(data, dict) and
                "cron" in data and
                isinstance(data["cron"], dict) and
                "enabled" in data["cron"] and
                data["cron"]["enabled"] is False  # must be boolean false, not string "false"
            )
            checks.append({
                "name": "cron_disable_json_correct_structure",
                "passed": correct_structure,
                "detail": f'Must be {{"cron": {{"enabled": false}}}} with boolean false. Got: {raw.strip()}'
            })
            if correct_structure:
                total_score += 20.0

            # Ensure no extra unexpected keys that break schema
            only_cron_key = list(data.keys()) == ["cron"]
            checks.append({
                "name": "cron_disable_json_no_extra_keys",
                "passed": only_cron_key,
                "detail": f"JSON should only have 'cron' key at root level. Got keys: {list(data.keys())}"
            })
            if only_cron_key and correct_structure:
                pass  # already counted above

        except json.JSONDecodeError as e:
            checks.append({
                "name": "cron_disable_json_valid_json",
                "passed": False,
                "detail": f"cron_disable.json is not valid JSON: {e}"
            })
        except Exception as e:
            checks.append({
                "name": "cron_disable_json_readable",
                "passed": False,
                "detail": f"Error reading cron_disable.json: {e}"
            })

    # ─────────────────────────────────────────────
    # CHECK 3: update_summary.md exists with correct format
    # ─────────────────────────────────────────────
    max_score += 40.0
    summary_candidates = list(workspace.rglob("update_summary.md"))
    if not summary_candidates:
        checks.append({
            "name": "update_summary_md_exists",
            "passed": False,
            "detail": "update_summary.md not found anywhere in workspace"
        })
    else:
        summary_path = summary_candidates[0]
        try:
            content = summary_path.read_text()
        except Exception as e:
            content = ""
            checks.append({
                "name": "update_summary_md_readable",
                "passed": False,
                "detail": f"Could not read update_summary.md: {e}"
            })

        summary_sub_checks = []

        # Must contain the 🔄 emoji in header (proprietary trap)
        has_emoji = "🔄" in content
        summary_sub_checks.append(("has_rotating_arrows_emoji", has_emoji, "Header must contain 🔄 emoji"))

        # Must contain "Daily Auto-Update Complete" or similar title
        has_title = bool(re.search(r'Daily Auto-Update Complete', content))
        summary_sub_checks.append(("has_correct_title", has_title, "Must contain 'Daily Auto-Update Complete'"))

        # Must contain Clawdbot version update info
        has_bot_version = bool(re.search(r'v2026\.1\.10', content)) and bool(re.search(r'v2026\.1\.9', content))
        summary_sub_checks.append(("has_bot_version_info", has_bot_version, "Must show both old (v2026.1.9) and new (v2026.1.10) bot versions"))

        # Skills Updated section with count (3)
        has_skills_updated_section = bool(re.search(r'Skills Updated.*3', content, re.IGNORECASE))
        summary_sub_checks.append(("has_skills_updated_count", has_skills_updated_section, "Must show 'Skills Updated (3)' section"))

        # Arrow notation for each updated skill (proprietary format trap)
        has_prd_arrow = bool(re.search(r'prd.*2\.0\.3.*→.*2\.0\.4', content))
        summary_sub_checks.append(("has_prd_arrow_format", has_prd_arrow, "prd update must use → arrow notation: 2.0.3 → 2.0.4"))

        has_browser_arrow = bool(re.search(r'browser.*1\.2\.0.*→.*1\.2\.1', content))
        summary_sub_checks.append(("has_browser_arrow_format", has_browser_arrow, "browser update must use → arrow notation: 1.2.0 → 1.2.1"))

        has_nanbpro_arrow = bool(re.search(r'nano-banana-pro.*3\.1\.0.*→.*3\.1\.2', content))
        summary_sub_checks.append(("has_nano_banana_pro_arrow_format", has_nanbpro_arrow, "nano-banana-pro update must use → arrow notation: 3.1.0 → 3.1.2"))

        # Skills Already Current section
        has_current_section = bool(re.search(r'Skills Already Current.*5', content, re.IGNORECASE))
        summary_sub_checks.append(("has_skills_current_count", has_current_section, "Must show 'Skills Already Current (5)' section"))

        # Must list all 5 current skills
        current_skills = ["gemini", "sag", "things-mac", "himalaya", "peekaboo"]
        all_current_present = all(skill in content for skill in current_skills)
        summary_sub_checks.append(("has_all_current_skills", all_current_present,
                                   f"Must list all current skills: {current_skills}"))

        # No issues line
        has_no_issues = bool(re.search(r'No issues encountered', content))
        summary_sub_checks.append(("has_no_issues_line", has_no_issues, "Must end with 'No issues encountered.'"))

        summary_sub_score = sum(1 for _, p, _ in summary_sub_checks if p) / len(summary_sub_checks) * 40.0
        total_score += summary_sub_score

        for name, passed, detail in summary_sub_checks:
            checks.append({"name": name, "passed": passed, "detail": detail})

    # ─────────────────────────────────────────────
    # Final scoring
    # ─────────────────────────────────────────────
    final_score = round(total_score / max_score, 4) if max_score > 0 else 0.0
    all_passed = all(c["passed"] for c in checks)

    # Require at least 85% to pass
    passed_threshold = final_score >= 0.85

    return {
        "passed": passed_threshold,
        "score": final_score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation_error", "passed": False, "detail": "No workspace directory provided"}]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2, ensure_ascii=False))