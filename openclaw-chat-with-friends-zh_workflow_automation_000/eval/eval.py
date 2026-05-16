import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    workspace = Path(workspace_dir)

    # Find AGENTS.md — must be in the workspace, likely in openclaw/ or root
    agents_files = list(workspace.rglob("AGENTS.md"))
    
    # Check 1: AGENTS.md exists
    check_exists = {
        "name": "AGENTS.md file exists",
        "passed": len(agents_files) > 0,
        "detail": f"Found {len(agents_files)} AGENTS.md file(s): {[str(f) for f in agents_files]}"
    }
    checks.append(check_exists)

    if not agents_files:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }

    # Use the first found AGENTS.md
    agents_path = agents_files[0]
    
    try:
        content = agents_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "AGENTS.md is readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    # Check 2: Contains channel name section (频道信息 or channel info heading)
    has_channel_info_section = bool(
        re.search(r'##\s*(频道信息|Channel Info|频道)', content, re.IGNORECASE)
    )
    checks.append({
        "name": "Contains channel info section (## 频道信息)",
        "passed": has_channel_info_section,
        "detail": f"Section header found: {has_channel_info_section}"
    })

    # Check 3: Contains the correct channel name "OpenClaw 宠物聊天室"
    has_channel_name = "OpenClaw 宠物聊天室" in content or "宠物聊天室" in content
    checks.append({
        "name": "Contains correct channel name (OpenClaw 宠物聊天室)",
        "passed": has_channel_name,
        "detail": f"Channel name present: {has_channel_name}"
    })

    # Check 4: Contains the correct Chat ID (-1001987654321)
    has_chat_id = "-1001987654321" in content
    checks.append({
        "name": "Contains correct Chat ID (-1001987654321)",
        "passed": has_chat_id,
        "detail": f"Chat ID found: {has_chat_id}"
    })

    # Check 5: Contains bot list section
    has_bot_section = bool(
        re.search(r'##\s*(频道中的机器人|机器人|Bots|Bot List)', content, re.IGNORECASE)
    )
    checks.append({
        "name": "Contains bot list section (## 频道中的机器人)",
        "passed": has_bot_section,
        "detail": f"Bot section found: {has_bot_section}"
    })

    # Check 6: Both bot names present — 爪爪 and 胡须
    has_pawsbot = "爪爪" in content
    has_whiskerbot = "胡须" in content
    has_both_bots = has_pawsbot and has_whiskerbot
    checks.append({
        "name": "Both bot names present (爪爪 and 胡须)",
        "passed": has_both_bots,
        "detail": f"爪爪: {has_pawsbot}, 胡须: {has_whiskerbot}"
    })

    # Check 7: Contains interaction rules section
    has_rules_section = bool(
        re.search(r'##\s*(互动规则|交互规则|规则|Interaction Rules|Rules)', content, re.IGNORECASE)
    )
    checks.append({
        "name": "Contains interaction rules section (## 互动规则)",
        "passed": has_rules_section,
        "detail": f"Rules section found: {has_rules_section}"
    })

    # Check 8: Name prefix rule — must describe format "名字：消息" or "爪爪：" style
    has_name_prefix_rule = bool(
        re.search(r'(名字.*冒号|冒号.*名字|前缀|爪爪：|格式.*：|：.*格式|name.*prefix|prefix.*name)', 
                  content, re.IGNORECASE)
    ) or ("：消息" in content) or ("爪爪：" in content) or ("名字加冒号" in content) or ("名字：" in content)
    checks.append({
        "name": "Name prefix rule present (bot_name: message format)",
        "passed": has_name_prefix_rule,
        "detail": f"Name prefix rule found: {has_name_prefix_rule}. Snippet: {content[:500]}"
    })

    # Check 9: 30-second cooldown rule
    has_30s_cooldown = bool(
        re.search(r'30\s*秒|30-second|30 second|间隔.*30|30.*间隔', content, re.IGNORECASE)
    )
    checks.append({
        "name": "30-second cooldown rule specified",
        "passed": has_30s_cooldown,
        "detail": f"30-second cooldown found: {has_30s_cooldown}"
    })

    # Check 10: 2-minute idle trigger rule
    has_2min_trigger = bool(
        re.search(r'2\s*分钟|two.?minute|2.?minute|2-minute|120\s*秒', content, re.IGNORECASE)
    )
    checks.append({
        "name": "2-minute idle trigger rule specified",
        "passed": has_2min_trigger,
        "detail": f"2-minute trigger found: {has_2min_trigger}"
    })

    # Check 11: Context window of 10 messages
    has_context_10 = bool(
        re.search(r'10\s*(条|messages|条消息)|最近.*10|10.*最近|context.*10|10.*context', 
                  content, re.IGNORECASE)
    )
    checks.append({
        "name": "Context window of 10 messages specified",
        "passed": has_context_10,
        "detail": f"10-message context window found: {has_context_10}"
    })

    # Check 12: Bot knows its own name is 爪爪
    has_self_identity = bool(
        re.search(r'(你的名字|自己的名字|名字是|my name|bot name).*爪爪|爪爪.*(你的名字|自己的名字|名字是|my name|bot name)', 
                  content, re.IGNORECASE)
    ) or bool(re.search(r'名字.*爪爪|爪爪.*名字', content))
    checks.append({
        "name": "Bot self-identity configured as 爪爪",
        "passed": has_self_identity,
        "detail": f"Self-identity rule found: {has_self_identity}"
    })

    # Check 13: Reply trigger control — only reply when named or after idle
    has_trigger_control = bool(
        re.search(r'(点名|被点名|被.*提及|named|mentioned|叫.*名字|name.*called).*才回复|只在.*回复|回复.*只在', 
                  content, re.IGNORECASE)
    ) or bool(re.search(r'(点名|触发|trigger|when.*named)', content, re.IGNORECASE))
    checks.append({
        "name": "Reply trigger control rule present (only when named)",
        "passed": has_trigger_control,
        "detail": f"Trigger control found: {has_trigger_control}"
    })

    # Check 14: Markdown format — must be proper markdown with ## headings
    has_markdown_headings = bool(re.search(r'^##\s+\S', content, re.MULTILINE))
    has_top_heading = bool(re.search(r'^#\s+\S', content, re.MULTILINE))
    is_markdown = has_markdown_headings and has_top_heading
    checks.append({
        "name": "File uses proper Markdown format with # and ## headings",
        "passed": is_markdown,
        "detail": f"Has ## headings: {has_markdown_headings}, Has # title: {has_top_heading}"
    })

    # Compute score
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = passed_checks / total_checks

    # Must pass critical checks to be considered passing overall
    critical_checks = [
        "AGENTS.md file exists",
        "Contains correct Chat ID (-1001987654321)",
        "Both bot names present (爪爪 and 胡须)",
        "30-second cooldown rule specified",
        "Context window of 10 messages specified",
        "Name prefix rule present (bot_name: message format)",
    ]
    
    critical_passed = all(
        any(c["name"] == cc and c["passed"] for c in checks)
        for cc in critical_checks
    )

    overall_passed = critical_passed and (score >= 0.75)

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))