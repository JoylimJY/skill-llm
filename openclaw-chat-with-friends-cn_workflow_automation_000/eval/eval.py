import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str) -> dict:
    checks = []
    
    workspace = Path(workspace_dir)
    
    # === CHECK 1: AGENTS.md exists somewhere in the workspace ===
    agents_files = list(workspace.rglob("AGENTS.md"))
    
    if not agents_files:
        checks.append({
            "name": "agents_md_exists",
            "passed": False,
            "detail": "No AGENTS.md file found anywhere in the workspace."
        })
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}
    
    # Use the first found (most relevant one - prefer openclaw directory)
    # Prioritize the one in openclaw directory
    target_file = None
    for f in agents_files:
        if "openclaw" in str(f):
            target_file = f
            break
    if target_file is None:
        target_file = agents_files[0]
    
    checks.append({
        "name": "agents_md_exists",
        "passed": True,
        "detail": f"Found AGENTS.md at: {target_file}"
    })
    
    # Read the file
    try:
        content = target_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({
            "name": "agents_md_readable",
            "passed": False,
            "detail": f"Could not read AGENTS.md: {e}"
        })
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append({
        "name": "agents_md_readable",
        "passed": True,
        "detail": "AGENTS.md is readable."
    })
    
    content_lower = content.lower()
    
    # === CHECK 2: Channel name PawChat is present ===
    has_pawchat = "pawchat" in content_lower
    checks.append({
        "name": "channel_name_pawchat",
        "passed": has_pawchat,
        "detail": "Channel name 'PawChat' found in AGENTS.md." if has_pawchat 
                  else "Channel name 'PawChat' NOT found in AGENTS.md. The config must reference the correct channel."
    })
    
    # === CHECK 3: Channel Chat ID is present (format: -100xxxxxxxxx) ===
    chat_id_pattern = re.search(r'-100\d{9,12}', content)
    has_chat_id = chat_id_pattern is not None
    checks.append({
        "name": "channel_chat_id_present",
        "passed": has_chat_id,
        "detail": f"Channel Chat ID found: {chat_id_pattern.group() if chat_id_pattern else 'N/A'}. "
                  + ("" if has_chat_id else "A valid Chat ID (format: -100xxxxxxxxxx) must be present.")
    })
    
    # === CHECK 4: CloudPaw bot name is listed ===
    has_cloudpaw = "cloudpaw" in content_lower
    checks.append({
        "name": "bot_cloudpaw_listed",
        "passed": has_cloudpaw,
        "detail": "Bot 'CloudPaw' found in AGENTS.md." if has_cloudpaw 
                  else "Bot 'CloudPaw' NOT found in AGENTS.md. All bots must be listed."
    })
    
    # === CHECK 5: SunnyTail bot name is listed ===
    has_sunnytail = "sunnytail" in content_lower
    checks.append({
        "name": "bot_sunnytail_listed",
        "passed": has_sunnytail,
        "detail": "Friend's bot 'SunnyTail' found in AGENTS.md." if has_sunnytail 
                  else "Friend's bot 'SunnyTail' NOT found in AGENTS.md. All channel bots must be listed."
    })
    
    # === CHECK 6: Name-prefix message format rule ===
    # Must have the "BotName：message" or "BotName: message" format rule
    # The skill mandates this EXACT format: name + colon prefix on EVERY message
    prefix_patterns = [
        r'名字.*?冒号',          # Chinese: name + colon
        r'前缀',                  # prefix in Chinese  
        r'cloudpaw\s*[：:]',     # CloudPaw: format example
        r'name.*?prefix',        # English variants
        r'prefix.*?name',
        r'每条消息.*?名字',       # every message must have name
        r'名字.*?每条',
        r'format.*?colon',
        r'colon.*?prefix',
        r'message.*?start.*?name',
        r'name.*?colon',
        r'cloudpaw：',           # actual example of format
    ]
    has_prefix_rule = any(re.search(p, content, re.IGNORECASE) for p in prefix_patterns)
    # Also check for explicit format demonstration
    format_demo = re.search(r'cloudpaw\s*[：:]\s*\S', content, re.IGNORECASE)
    has_prefix_rule = has_prefix_rule or (format_demo is not None)
    
    checks.append({
        "name": "message_prefix_format_rule",
        "passed": has_prefix_rule,
        "detail": "Message name-prefix format rule found (e.g., 'CloudPaw：message content')." if has_prefix_rule 
                  else "CRITICAL: Missing mandatory message prefix rule. Every bot message must start with 'BotName：message'. This is the key anti-ambiguity rule."
    })
    
    # === CHECK 7: Cooldown / frequency limit (≥30 seconds) ===
    # Must have cooldown between 30 seconds minimum
    cooldown_patterns = [
        r'30\s*秒',       # 30 seconds Chinese
        r'30\s*second',   # 30 seconds English
        r'冷却',           # cooldown Chinese
        r'cooldown',
        r'频率.*?限制',
        r'interval.*?30',
        r'30.*?interval',
        r'minimum.*?30',
        r'30.*?minimum',
        r'至少.*?30',     # at least 30
        r'30.*?至少',
    ]
    has_cooldown = any(re.search(p, content, re.IGNORECASE) for p in cooldown_patterns)
    checks.append({
        "name": "cooldown_30_seconds",
        "passed": has_cooldown,
        "detail": "Cooldown rule (≥30 seconds between replies) found." if has_cooldown 
                  else "Missing cooldown rule. Must specify at least 30 seconds between bot replies to prevent message loops."
    })
    
    # === CHECK 8: Context window (10 messages) ===
    context_patterns = [
        r'10\s*条',          # 10 messages Chinese
        r'最近.*?10',        # recent 10
        r'10.*?消息',
        r'10.*?message',
        r'message.*?10',
        r'context.*?10',
        r'10.*?context',
        r'window.*?10',
        r'10.*?window',
        r'上下文.*?10',      # context window Chinese
        r'10.*?上下文',
    ]
    has_context = any(re.search(p, content, re.IGNORECASE) for p in context_patterns)
    checks.append({
        "name": "context_window_10_messages",
        "passed": has_context,
        "detail": "Context window (10 messages) rule found." if has_context 
                  else "Missing context window rule. Must specify reading last 10 messages for conversational coherence."
    })
    
    # === CHECK 9: Reply trigger rule (only when mentioned OR after 2 min silence) ===
    trigger_patterns = [
        r'被点名',              # when mentioned
        r'2\s*分钟',            # 2 minutes
        r'被.*?呼叫',
        r'点名.*?回复',
        r'only.*?mention',
        r'mention.*?reply',
        r'when.*?mention',
        r'2.*?minute',
        r'minute.*?2',
        r'silence.*?2',
        r'2.*?silence',
        r'触发',                # trigger
        r'reply.*?trigger',
        r'trigger.*?reply',
        r'回复.*?触发',
    ]
    has_trigger = any(re.search(p, content, re.IGNORECASE) for p in trigger_patterns)
    checks.append({
        "name": "reply_trigger_rule",
        "passed": has_trigger,
        "detail": "Reply trigger rule found (e.g., only reply when mentioned or after 2 min silence)." if has_trigger 
                  else "Missing reply trigger rule. Must define when bot replies (e.g., when mentioned, or after 2 minutes of silence)."
    })
    
    # === CHECK 10: Bot self-identity rule ===
    identity_patterns = [
        r'你的名字是',          # your name is (Chinese)
        r'your name is',
        r'i am cloudpaw',
        r'我是.*?cloudpaw',
        r'自己的名字',          # own name
        r'身份.*?cloudpaw',
        r'cloudpaw.*?身份',
        r'name.*?cloudpaw',
        r'cloudpaw.*?name',
        r'identity.*?cloudpaw',
    ]
    has_identity = any(re.search(p, content, re.IGNORECASE) for p in identity_patterns)
    checks.append({
        "name": "bot_self_identity",
        "passed": has_identity,
        "detail": "Bot self-identity rule found (bot knows its own name is CloudPaw)." if has_identity 
                  else "Missing bot self-identity rule. Bot must know its own name (CloudPaw) for proper prefix usage."
    })
    
    # === CHECK 11: The stub/wrong AGENTS.md content has been replaced ===
    # The original stub just said "Just be helpful and friendly. Reply to everything."
    # Ensure it's been properly replaced with channel-specific rules
    has_stub_content = "reply to everything" in content_lower or (
        "just be helpful" in content_lower and len(content.strip()) < 100
    )
    is_substantially_updated = len(content.strip()) > 300  # Must be substantial
    checks.append({
        "name": "stub_content_replaced",
        "passed": (not has_stub_content) and is_substantially_updated,
        "detail": "AGENTS.md has been substantially updated with proper channel rules." 
                  if (not has_stub_content) and is_substantially_updated
                  else f"AGENTS.md appears to still contain stub content or is too short ({len(content.strip())} chars). Must have comprehensive channel rules."
    })
    
    # === FINAL SCORING ===
    check_weights = {
        "agents_md_exists": 0.05,
        "agents_md_readable": 0.05,
        "channel_name_pawchat": 0.08,
        "channel_chat_id_present": 0.08,
        "bot_cloudpaw_listed": 0.08,
        "bot_sunnytail_listed": 0.08,
        "message_prefix_format_rule": 0.15,  # Most critical proprietary rule
        "cooldown_30_seconds": 0.12,
        "context_window_10_messages": 0.10,
        "reply_trigger_rule": 0.10,
        "bot_self_identity": 0.07,
        "stub_content_replaced": 0.04,
    }
    
    total_score = 0.0
    for check in checks:
        weight = check_weights.get(check["name"], 0.0)
        if check["passed"]:
            total_score += weight
    
    # Must pass critical checks to overall pass
    critical_checks = [
        "agents_md_exists",
        "message_prefix_format_rule",
        "bot_cloudpaw_listed",
        "bot_sunnytail_listed",
        "cooldown_30_seconds",
    ]
    critical_passed = all(
        next((c["passed"] for c in checks if c["name"] == name), False)
        for name in critical_checks
    )
    
    overall_passed = critical_passed and total_score >= 0.70
    
    return {
        "passed": overall_passed,
        "score": round(total_score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided."}]}))
        sys.exit(1)
    
    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))