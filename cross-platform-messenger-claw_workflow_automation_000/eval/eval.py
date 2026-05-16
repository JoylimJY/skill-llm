#!/usr/bin/env python3
import sys
import json
import requests

def get_calls():
    try:
        r = requests.get("http://127.0.0.1:19876/calls", timeout=5)
        return r.json()
    except Exception as e:
        return []

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    calls = get_calls()

    checks = []
    overall_passed = True

    # Helper: find calls matching channel
    def find_calls(channel):
        return [c for c in calls if c.get("channel") == channel]

    def find_calls_channel_target(channel, target_substr):
        return [c for c in calls if c.get("channel") == channel and target_substr in str(c.get("target", ""))]

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 1: Feishu group — target must start with "oc_" prefix
    # Raw ID in brief: c_9f3a2b1d7e04 → correct: oc_c_9f3a2b1d7e04
    # ─────────────────────────────────────────────────────────────────────────
    feishu_calls = find_calls("feishu")
    feishu_ok = False
    feishu_detail = "No feishu calls found."
    for c in feishu_calls:
        target = str(c.get("target", ""))
        if target.startswith("oc_") and "9f3a2b1d7e04" in target:
            feishu_ok = True
            feishu_detail = f"Feishu group call found with correct oc_ prefix: target={target}"
            break
    if not feishu_ok:
        # Check if they used wrong prefix or wrong ID
        for c in feishu_calls:
            feishu_detail = f"Feishu call found but target={c.get('target','?')} — expected oc_ prefix with 9f3a2b1d7e04"
        overall_passed = False

    checks.append({
        "name": "feishu_group_oc_prefix",
        "passed": feishu_ok,
        "detail": feishu_detail
    })

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 2: Discord — target must be "channel:<snowflake_id>"
    # Raw ID: 987654321098765432 → correct: channel:987654321098765432
    # ─────────────────────────────────────────────────────────────────────────
    discord_calls = find_calls("discord")
    discord_target_ok = False
    discord_detail = "No discord calls found."
    for c in discord_calls:
        target = str(c.get("target", ""))
        if target == "channel:987654321098765432":
            discord_target_ok = True
            discord_detail = f"Discord call found with correct channel: prefix: target={target}"
            break
    if not discord_target_ok:
        for c in discord_calls:
            discord_detail = f"Discord call found but target={c.get('target','?')} — expected channel:987654321098765432"
        overall_passed = False

    checks.append({
        "name": "discord_channel_prefix_format",
        "passed": discord_target_ok,
        "detail": discord_detail
    })

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 3: Discord — must be sent with --silent flag
    # ─────────────────────────────────────────────────────────────────────────
    discord_silent_ok = False
    discord_silent_detail = "No discord calls with --silent found."
    for c in discord_calls:
        target = str(c.get("target", ""))
        if "987654321098765432" in target and c.get("silent") is True:
            discord_silent_ok = True
            discord_silent_detail = "Discord call has silent=True as required."
            break
    if not discord_silent_ok:
        for c in discord_calls:
            discord_silent_detail = f"Discord call found but silent={c.get('silent', 'missing')} — should be True"
        overall_passed = False

    checks.append({
        "name": "discord_silent_flag",
        "passed": discord_silent_ok,
        "detail": discord_silent_detail
    })

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 4: Telegram — group must use NEGATIVE chat_id
    # Raw ID: 1001234567890 → correct: -1001234567890
    # ─────────────────────────────────────────────────────────────────────────
    telegram_calls = find_calls("telegram")
    telegram_negative_ok = False
    telegram_detail = "No telegram calls found."
    for c in telegram_calls:
        target = str(c.get("target", ""))
        # Accept -1001234567890 or -100_1234567890 as long as it's negative and contains the digits
        try:
            t_val = int(target)
            if t_val < 0 and "1234567890" in target:
                telegram_negative_ok = True
                telegram_detail = f"Telegram call found with correct negative group ID: target={target}"
                break
        except (ValueError, TypeError):
            pass
    if not telegram_negative_ok:
        for c in telegram_calls:
            telegram_detail = f"Telegram call found but target={c.get('target','?')} — expected negative int like -1001234567890"
        overall_passed = False

    checks.append({
        "name": "telegram_group_negative_id",
        "passed": telegram_negative_ok,
        "detail": telegram_detail
    })

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 5: Telegram — must be sent with --silent flag
    # ─────────────────────────────────────────────────────────────────────────
    telegram_silent_ok = False
    telegram_silent_detail = "No telegram calls with --silent found."
    for c in telegram_calls:
        if c.get("silent") is True:
            telegram_silent_ok = True
            telegram_silent_detail = "Telegram call has silent=True as required."
            break
    if not telegram_silent_ok:
        for c in telegram_calls:
            telegram_silent_detail = f"Telegram call found but silent={c.get('silent', 'missing')} — should be True"
        overall_passed = False

    checks.append({
        "name": "telegram_silent_flag",
        "passed": telegram_silent_ok,
        "detail": telegram_silent_detail
    })

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 6: WhatsApp — must use E.164 format with +86 country code
    # Raw: 13912345678 → correct: +8613912345678
    # ─────────────────────────────────────────────────────────────────────────
    whatsapp_calls = find_calls("whatsapp")
    whatsapp_ok = False
    whatsapp_detail = "No whatsapp calls found."
    for c in whatsapp_calls:
        target = str(c.get("target", ""))
        if target == "+8613912345678":
            whatsapp_ok = True
            whatsapp_detail = f"WhatsApp call found with correct E.164 format: target={target}"
            break
    if not whatsapp_ok:
        for c in whatsapp_calls:
            whatsapp_detail = f"WhatsApp call found but target={c.get('target','?')} — expected +8613912345678"
        overall_passed = False

    checks.append({
        "name": "whatsapp_e164_format",
        "passed": whatsapp_ok,
        "detail": whatsapp_detail
    })

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 7: Slack — target must be #incidents
    # ─────────────────────────────────────────────────────────────────────────
    slack_calls = find_calls("slack")
    slack_ok = False
    slack_detail = "No slack calls found."
    for c in slack_calls:
        target = str(c.get("target", ""))
        if target == "#incidents":
            slack_ok = True
            slack_detail = f"Slack call found with correct target: target={target}"
            break
    if not slack_ok:
        for c in slack_calls:
            slack_detail = f"Slack call found but target={c.get('target','?')} — expected #incidents"
        overall_passed = False

    checks.append({
        "name": "slack_channel_format",
        "passed": slack_ok,
        "detail": slack_detail
    })

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 8: All 5 channels sent the correct alert message (keyword check)
    # ─────────────────────────────────────────────────────────────────────────
    alert_keyword = "INC-2042"
    all_channels = ["feishu", "discord", "telegram", "whatsapp", "slack"]
    message_ok_count = 0
    missing_msg_channels = []
    for ch in all_channels:
        ch_calls = find_calls(ch)
        found_msg = any(alert_keyword in str(c.get("message", "")) for c in ch_calls)
        if found_msg:
            message_ok_count += 1
        else:
            missing_msg_channels.append(ch)

    message_ok = (message_ok_count == 5)
    if not message_ok:
        overall_passed = False

    checks.append({
        "name": "all_channels_correct_message",
        "passed": message_ok,
        "detail": f"{message_ok_count}/5 channels received message containing '{alert_keyword}'. Missing: {missing_msg_channels}"
    })

    # ─────────────────────────────────────────────────────────────────────────
    # Final score
    # ─────────────────────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / len(checks), 3)
    overall_passed = all(c["passed"] for c in checks)

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()