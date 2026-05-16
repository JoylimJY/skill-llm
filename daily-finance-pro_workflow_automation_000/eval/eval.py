#!/usr/bin/env python3
import sys
import json
import re
from pathlib import Path

def load_json_safe(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f), None
    except Exception as e:
        return None, str(e)

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    checks = []
    
    # ─────────────────────────────────────────────
    # CHECK 1: openclaw cron add was called
    # ─────────────────────────────────────────────
    log_path = workspace / "openclaw_command_log.json"
    log_data, err = load_json_safe(log_path)
    
    cron_add_cmd = None
    cron_run_cmd = None
    
    if log_data is None:
        checks.append({
            "name": "openclaw_command_log_exists",
            "passed": False,
            "detail": f"Could not load command log: {err}"
        })
    else:
        checks.append({
            "name": "openclaw_command_log_exists",
            "passed": True,
            "detail": "Command log loaded successfully"
        })
        
        for cmd in log_data.get("commands", []):
            if cmd.get("subcommand") == "cron_add":
                cron_add_cmd = cmd
            if cmd.get("subcommand") == "cron_run":
                cron_run_cmd = cmd

    # ─────────────────────────────────────────────
    # CHECK 2: cron add was invoked
    # ─────────────────────────────────────────────
    if cron_add_cmd is None:
        checks.append({
            "name": "cron_add_invoked",
            "passed": False,
            "detail": "No 'openclaw cron add' command found in the log."
        })
    else:
        checks.append({
            "name": "cron_add_invoked",
            "passed": True,
            "detail": f"cron add found: {cron_add_cmd.get('raw_command','')}"
        })

    # ─────────────────────────────────────────────
    # CHECK 3: Correct --name parameter
    # ─────────────────────────────────────────────
    if cron_add_cmd:
        params = cron_add_cmd.get("parsed_params", {})
        expected_name = "每日财经推送"
        actual_name = params.get("name", "")
        name_ok = actual_name == expected_name
        checks.append({
            "name": "cron_name_correct",
            "passed": name_ok,
            "detail": f"Expected name='每日财经推送', got='{actual_name}'"
        })
    else:
        checks.append({
            "name": "cron_name_correct",
            "passed": False,
            "detail": "cron add not invoked, cannot check name"
        })

    # ─────────────────────────────────────────────
    # CHECK 4: Correct --agent parameter
    # ─────────────────────────────────────────────
    if cron_add_cmd:
        params = cron_add_cmd.get("parsed_params", {})
        agent_ok = params.get("agent", "") == "main"
        checks.append({
            "name": "cron_agent_correct",
            "passed": agent_ok,
            "detail": f"Expected agent='main', got='{params.get('agent', '')}'"
        })
    else:
        checks.append({
            "name": "cron_agent_correct",
            "passed": False,
            "detail": "cron add not invoked"
        })

    # ─────────────────────────────────────────────
    # CHECK 5: Correct --channel parameter
    # ─────────────────────────────────────────────
    if cron_add_cmd:
        params = cron_add_cmd.get("parsed_params", {})
        channel_ok = params.get("channel", "") == "feishu"
        checks.append({
            "name": "cron_channel_correct",
            "passed": channel_ok,
            "detail": f"Expected channel='feishu', got='{params.get('channel', '')}'"
        })
    else:
        checks.append({
            "name": "cron_channel_correct",
            "passed": False,
            "detail": "cron add not invoked"
        })

    # ─────────────────────────────────────────────
    # CHECK 6: CRITICAL - UTC timezone conversion for 06:30 Beijing
    # Beijing 06:30 = UTC 22:30 (previous day) = cron "30 22 * * *"
    # ─────────────────────────────────────────────
    if cron_add_cmd:
        params = cron_add_cmd.get("parsed_params", {})
        schedule = params.get("schedule", "")
        
        # Beijing 06:30 = UTC-8 = 22:30 UTC
        # Correct cron: "30 22 * * *"
        correct_schedule = "30 22 * * *"
        wrong_schedule_beijing = "30 6 * * *"   # naive mistake
        wrong_schedule_other = "30 30 * * *"    # nonsense
        
        schedule_ok = schedule.strip() == correct_schedule
        
        detail = f"Expected schedule='{correct_schedule}' (6:30 Beijing = 22:30 UTC), got='{schedule}'"
        if schedule.strip() == wrong_schedule_beijing:
            detail += " | FAIL: Agent used Beijing time directly without UTC conversion!"
        
        checks.append({
            "name": "cron_schedule_utc_conversion_correct",
            "passed": schedule_ok,
            "detail": detail
        })
    else:
        checks.append({
            "name": "cron_schedule_utc_conversion_correct",
            "passed": False,
            "detail": "cron add not invoked, cannot check schedule"
        })

    # ─────────────────────────────────────────────
    # CHECK 7: cron run --preview was called
    # ─────────────────────────────────────────────
    if cron_run_cmd is None:
        checks.append({
            "name": "cron_run_preview_invoked",
            "passed": False,
            "detail": "No 'openclaw cron run ... --preview' command found in log."
        })
    else:
        preview_ok = cron_run_cmd.get("preview", False)
        job_name_ok = cron_run_cmd.get("job_name", "") == "每日财经推送"
        ok = preview_ok and job_name_ok
        checks.append({
            "name": "cron_run_preview_invoked",
            "passed": ok,
            "detail": f"cron run found. preview={preview_ok}, job_name='{cron_run_cmd.get('job_name','')}'"
        })

    # ─────────────────────────────────────────────
    # CHECK 8: push_content.txt exists
    # ─────────────────────────────────────────────
    push_file_candidates = list(workspace.rglob("push_content.txt"))
    if not push_file_candidates:
        push_content = None
        checks.append({
            "name": "push_content_file_exists",
            "passed": False,
            "detail": "push_content.txt not found anywhere in workspace"
        })
    else:
        try:
            push_content = push_file_candidates[0].read_text(encoding="utf-8")
            checks.append({
                "name": "push_content_file_exists",
                "passed": True,
                "detail": f"Found at {push_file_candidates[0]}, length={len(push_content)} chars"
            })
        except Exception as e:
            push_content = None
            checks.append({
                "name": "push_content_file_exists",
                "passed": False,
                "detail": f"Error reading push_content.txt: {e}"
            })

    # ─────────────────────────────────────────────
    # CHECK 9: push_content header format (💹 财经早参)
    # ─────────────────────────────────────────────
    if push_content:
        header_ok = "💹" in push_content and ("财经早参" in push_content or "财经" in push_content)
        checks.append({
            "name": "push_content_header_format",
            "passed": header_ok,
            "detail": f"Header check: has '💹'={'💹' in push_content}, has '财经早参'={'财经早参' in push_content}"
        })
    else:
        checks.append({
            "name": "push_content_header_format",
            "passed": False,
            "detail": "push_content.txt not available"
        })

    # ─────────────────────────────────────────────
    # CHECK 10: Sentiment indicator - one of the 4 proprietary emojis present
    # Based on market data: 4200+ stocks up, clear bullish → ☀️
    # ─────────────────────────────────────────────
    if push_content:
        sentiment_emojis = ["☀️", "🌙", "⚖️", "🔥"]
        found_sentiments = [e for e in sentiment_emojis if e in push_content]
        has_sentiment = len(found_sentiments) > 0
        
        # Based on market data: 4200 stocks up vs 600 down (>3000 single-side) → ☀️ bullish
        # We'll accept any valid sentiment emoji, but check that exactly one type is present
        # Primary check: at least one proprietary sentiment emoji is present
        checks.append({
            "name": "push_content_sentiment_indicator_present",
            "passed": has_sentiment,
            "detail": f"Found sentiment emojis: {found_sentiments}. Valid emojis are {sentiment_emojis}"
        })
        
        # Secondary check: Given data (4200 up vs 600 down >> 3000 threshold), ☀️ is correct
        correct_sentiment = "☀️" in push_content
        checks.append({
            "name": "push_content_sentiment_indicator_bullish",
            "passed": correct_sentiment,
            "detail": f"Market data shows 4200 up vs 600 down (>3000 single-side threshold), expected ☀️ (加仓信号). Found: {found_sentiments}"
        })
    else:
        checks.append({
            "name": "push_content_sentiment_indicator_present",
            "passed": False,
            "detail": "push_content.txt not available"
        })
        checks.append({
            "name": "push_content_sentiment_indicator_bullish",
            "passed": False,
            "detail": "push_content.txt not available"
        })

    # ─────────────────────────────────────────────
    # CHECK 11: Item count 5-7 (numbered items)
    # ─────────────────────────────────────────────
    if push_content:
        # Count numbered list items (lines starting with 1. 2. 3. etc.)
        numbered_items = re.findall(r'^\s*[1-9]\d*[\.\、]\s+.+', push_content, re.MULTILINE)
        item_count = len(numbered_items)
        item_count_ok = 5 <= item_count <= 7
        checks.append({
            "name": "push_content_item_count_5_to_7",
            "passed": item_count_ok,
            "detail": f"Found {item_count} numbered items. Required: 5-7. Items found: {numbered_items}"
        })
    else:
        checks.append({
            "name": "push_content_item_count_5_to_7",
            "passed": False,
            "detail": "push_content.txt not available"
        })

    # ─────────────────────────────────────────────
    # CHECK 12: Source footer present
    # ─────────────────────────────────────────────
    if push_content:
        has_source = "来源" in push_content and ("华尔街见闻" in push_content or "雪球" in push_content)
        checks.append({
            "name": "push_content_source_footer",
            "passed": has_source,
            "detail": f"Source footer check: has '来源'={'来源' in push_content}, has '华尔街见闻'={'华尔街见闻' in push_content}"
        })
    else:
        checks.append({
            "name": "push_content_source_footer",
            "passed": False,
            "detail": "push_content.txt not available"
        })

    # ─────────────────────────────────────────────
    # CHECK 13: Total character count under 500
    # ─────────────────────────────────────────────
    if push_content:
        char_count = len(push_content)
        under_limit = char_count <= 500
        checks.append({
            "name": "push_content_under_500_chars",
            "passed": under_limit,
            "detail": f"Total characters: {char_count}. Limit: 500."
        })
    else:
        checks.append({
            "name": "push_content_under_500_chars",
            "passed": False,
            "detail": "push_content.txt not available"
        })

    # ─────────────────────────────────────────────
    # SCORING
    # ─────────────────────────────────────────────
    # Critical checks (must pass): UTC conversion, cron invoked, push file exists, sentiment
    critical_checks = [
        "cron_add_invoked",
        "cron_schedule_utc_conversion_correct",
        "cron_name_correct",
        "push_content_file_exists",
        "push_content_sentiment_indicator_present",
        "push_content_item_count_5_to_7",
    ]
    
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    
    critical_passed = all(
        next((c["passed"] for c in checks if c["name"] == name), False)
        for name in critical_checks
    )
    
    score = passed_count / total if total > 0 else 0.0
    overall_passed = critical_passed and score >= 0.75
    
    result = {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()