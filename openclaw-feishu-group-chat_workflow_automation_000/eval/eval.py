import sys
import json
import re
import subprocess
from pathlib import Path

def load_file(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception as e:
        return None

def run_eval(workspace):
    checks = []
    
    workspace = Path(workspace)
    user_md_path = workspace / "USER.md"
    agents_md_path = workspace / "AGENTS.md"
    soul_md_path = workspace / "SOUL.md"
    
    user_md = load_file(user_md_path)
    agents_md = load_file(agents_md_path)
    soul_md = load_file(soul_md_path)
    combined_agent_soul = (agents_md or "") + "\n" + (soul_md or "")

    # ----------------------------------------------------------------
    # CHECK 1: USER.md contains the 飞书通讯录 section header (Chinese)
    # ----------------------------------------------------------------
    check_name = "USER.md has Chinese 飞书通讯录 section header"
    try:
        if user_md and "飞书通讯录" in user_md:
            checks.append({"name": check_name, "passed": True, "detail": "Section header found in USER.md"})
        else:
            checks.append({"name": check_name, "passed": False, "detail": "Missing '飞书通讯录' section in USER.md. The sync script must be run to populate this."})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ----------------------------------------------------------------
    # CHECK 2: USER.md contact table has correct Chinese column headers
    # ----------------------------------------------------------------
    check_name = "USER.md contact table has correct Chinese column headers (姓名 | open_id)"
    try:
        if user_md and "| 姓名 | open_id |" in user_md:
            checks.append({"name": check_name, "passed": True, "detail": "Correct Chinese column headers found"})
        else:
            checks.append({"name": check_name, "passed": False, "detail": "Missing '| 姓名 | open_id |' table headers. Table must use Chinese header for name column."})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ----------------------------------------------------------------
    # CHECK 3: USER.md has the explanatory Chinese text about chat_id format user:ou_xxx
    # ----------------------------------------------------------------
    check_name = "USER.md has Chinese explanation about chat_id format user:ou_xxx"
    try:
        if user_md and "chat_id" in user_md and "user:ou_xxx" in user_md:
            checks.append({"name": check_name, "passed": True, "detail": "chat_id explanation with user:ou_xxx format found"})
        else:
            checks.append({"name": check_name, "passed": False, "detail": "Missing explanatory text about chat_id format 'user:ou_xxx' — this should come from running the sync script."})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ----------------------------------------------------------------
    # CHECK 4: USER.md contains actual contact entries (open_ids)
    # ----------------------------------------------------------------
    check_name = "USER.md contains actual contact open_id entries"
    try:
        if user_md and "ou_" in user_md:
            # Count how many ou_ entries exist
            matches = re.findall(r'ou_[a-zA-Z0-9]+', user_md)
            if len(matches) >= 3:
                checks.append({"name": check_name, "passed": True, "detail": f"Found {len(matches)} open_id entries in USER.md"})
            else:
                checks.append({"name": check_name, "passed": False, "detail": f"Only {len(matches)} open_id entries found; expected at least 3"})
        else:
            checks.append({"name": check_name, "passed": False, "detail": "No open_id entries (ou_xxx) found in USER.md"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ----------------------------------------------------------------
    # CHECK 5: AGENTS.md or SOUL.md has Chinese sender identification snippet
    # mentioning open_id extraction from user:ou_xxx format
    # ----------------------------------------------------------------
    check_name = "AGENTS.md or SOUL.md has Chinese sender identification snippet with open_id and user:ou_xxx"
    try:
        has_open_id_mention = "open_id" in combined_agent_soul
        has_chat_id_format = "user:ou_xxx" in combined_agent_soul or "ou_xxx" in combined_agent_soul
        has_dm_warning = any(phrase in combined_agent_soul for phrase in [
            "不要假设", "DM 不携带", "飞书 DM", "inbound metadata"
        ])
        if has_open_id_mention and has_chat_id_format and has_dm_warning:
            checks.append({"name": check_name, "passed": True, "detail": "Chinese sender identification snippet found with all required elements"})
        else:
            missing = []
            if not has_open_id_mention: missing.append("open_id mention")
            if not has_chat_id_format: missing.append("user:ou_xxx format")
            if not has_dm_warning: missing.append("Chinese warning about DM assumption")
            checks.append({"name": check_name, "passed": False, "detail": f"Missing: {', '.join(missing)}"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ----------------------------------------------------------------
    # CHECK 6: AGENTS.md or SOUL.md has group chat etiquette rules
    # (respond when @mentioned, stay silent for banter, one reaction max)
    # ----------------------------------------------------------------
    check_name = "AGENTS.md or SOUL.md has group chat etiquette rules"
    try:
        etiquette_signals = [
            "@",  # @mentioned concept
        ]
        silence_signals = [
            "silent", "silence", "stay silent", "banter", "不回应", "沉默", "casual"
        ]
        concise_signals = [
            "concise", "brief", "简洁", "one reaction", "monologue", "dominate"
        ]
        has_mention = any(s in combined_agent_soul for s in etiquette_signals)
        has_silence = any(s in combined_agent_soul for s in silence_signals)
        has_concise = any(s in combined_agent_soul for s in concise_signals)
        
        if has_mention and has_silence and has_concise:
            checks.append({"name": check_name, "passed": True, "detail": "Group chat etiquette rules found (respond when mentioned, silence for banter, concise replies)"})
        else:
            missing = []
            if not has_mention: missing.append("@mention trigger")
            if not has_silence: missing.append("stay silent for banter rule")
            if not has_concise: missing.append("concise/no-monologue rule")
            checks.append({"name": check_name, "passed": False, "detail": f"Missing etiquette elements: {', '.join(missing)}"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ----------------------------------------------------------------
    # CHECK 7: AGENTS.md or SOUL.md explicitly forbids Markdown formatting
    # (no **bold**, no # headers, no [link](url), no tables)
    # ----------------------------------------------------------------
    check_name = "AGENTS.md or SOUL.md contains Feishu no-markdown formatting rule"
    try:
        no_markdown_signals = [
            "No markdown", "no markdown", "no Markdown",
            "no **bold**", "No **bold**",
            "No markdown", "plain text", "plain-text",
            "Feishu does not render", "不支持 Markdown", "不用 markdown",
            "no tables", "No tables", "不使用表格"
        ]
        has_no_md = any(s in combined_agent_soul for s in no_markdown_signals)
        
        # Also check for explicit mention of code blocks being OK (sparingly)
        has_code_ok = "code block" in combined_agent_soul or "```" in combined_agent_soul
        
        if has_no_md:
            detail = "No-markdown rule found."
            if has_code_ok:
                detail += " Code block exception also documented."
            checks.append({"name": check_name, "passed": True, "detail": detail})
        else:
            checks.append({"name": check_name, "passed": False, "detail": "No explicit Feishu anti-markdown rule found in AGENTS.md or SOUL.md. Must state no markdown, no bold, no headers, no tables, plain text only."})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ----------------------------------------------------------------
    # CHECK 8: AGENTS.md or SOUL.md has multi-user privacy rules
    # (conversations isolated, don't leak A's info to B)
    # ----------------------------------------------------------------
    check_name = "AGENTS.md or SOUL.md has multi-user privacy/isolation rules"
    try:
        privacy_signals = [
            "isolated", "isolation", "private", "privacy",
            "don't reveal", "never reveal", "never leak", "not share",
            "don't share", "隔离", "泄露", "私密", "A said", "person A", "person B",
            "what A", "leak what"
        ]
        has_privacy = any(s in combined_agent_soul for s in privacy_signals)
        if has_privacy:
            checks.append({"name": check_name, "passed": True, "detail": "Multi-user privacy/isolation rule found"})
        else:
            checks.append({"name": check_name, "passed": False, "detail": "No multi-user privacy rules found. Must include: conversations are isolated, don't reveal user A's info to user B."})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ----------------------------------------------------------------
    # CHECK 9: Weekly crontab entry with EXACT schedule 0 7 * * 1
    # and correct script path and arguments pattern
    # ----------------------------------------------------------------
    check_name = "Crontab has weekly Monday 7am sync entry (0 7 * * 1) with correct script"
    try:
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        crontab_content = result.stdout
        
        # Look for the 0 7 * * 1 pattern
        cron_pattern = re.compile(r'0\s+7\s+\*\s+\*\s+1.*sync_feishu_contacts\.py', re.MULTILINE)
        match = cron_pattern.search(crontab_content)
        
        if match:
            line = match.group(0)
            # Verify it includes the script and looks like it passes 3 args (config, account, user_md)
            checks.append({"name": check_name, "passed": True, "detail": f"Found crontab entry: {line[:120]}"})
        else:
            # Also check common crontab file locations
            found = False
            for cron_file in ["/etc/cron.d/openclaw", "/var/spool/cron/crontabs/root", "/tmp/openclaw_cron"]:
                try:
                    content = Path(cron_file).read_text()
                    if re.search(r'0\s+7\s+\*\s+\*\s+1.*sync_feishu_contacts', content):
                        found = True
                        checks.append({"name": check_name, "passed": True, "detail": f"Found crontab entry in {cron_file}"})
                        break
                except:
                    pass
            if not found:
                checks.append({"name": check_name, "passed": False, "detail": f"No crontab entry matching '0 7 * * 1 ...sync_feishu_contacts.py' found. Crontab output: {crontab_content[:200] if crontab_content else 'empty'}"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Could not read crontab: {str(e)}"})

    # ----------------------------------------------------------------
    # CHECK 10: DM behavior rules present (address by name, not primary human assumption)
    # ----------------------------------------------------------------
    check_name = "AGENTS.md or SOUL.md has DM behavior rules (address by name, anyone can DM)"
    try:
        dm_signals_name = [
            "actual name", "by name", "by their name", "sender.*name", "address.*name",
            "姓名", "叫对方名字", "实际姓名"
        ]
        dm_signals_anyone = [
            "anyone can", "any user", "not your primary", "not the primary", 
            "主人", "不是主人", "任何人", "anyone", "any person"
        ]
        has_name_rule = any(
            re.search(s, combined_agent_soul, re.IGNORECASE) 
            for s in dm_signals_name
        )
        has_anyone_rule = any(s in combined_agent_soul for s in dm_signals_anyone)
        
        if has_name_rule and has_anyone_rule:
            checks.append({"name": check_name, "passed": True, "detail": "DM rules found: address by name + anyone-can-DM warning"})
        elif has_name_rule or has_anyone_rule:
            checks.append({"name": check_name, "passed": False, "detail": f"Partial DM rules: name_rule={has_name_rule}, anyone_rule={has_anyone_rule}. Both required."})
        else:
            checks.append({"name": check_name, "passed": False, "detail": "No DM behavior rules found. Must include: address sender by name, never assume DM is from primary human."})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ----------------------------------------------------------------
    # Final scoring
    # ----------------------------------------------------------------
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    overall_passed = passed_count >= 8  # Must pass at least 8/10

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    
    result = run_eval(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))