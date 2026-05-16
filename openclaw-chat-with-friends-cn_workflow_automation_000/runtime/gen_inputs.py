import os
import random

random.seed(42)

workspace = "/workspace"

# Build a realistic deeply-nested directory structure simulating an OpenClaw installation
dirs = [
    "openclaw/config",
    "openclaw/logs",
    "openclaw/plugins",
    "openclaw/sessions/active",
    "openclaw/sessions/archived",
    "openclaw/channels",
    "openclaw/bots/cloudpaw",
    "openclaw/bots/cloudpaw/memory",
    "openclaw/bots/cloudpaw/prompts",
    "openclaw/data/exports",
    "openclaw/data/imports",
    "telegram/webhooks",
    "telegram/bot_profiles",
    "docs/setup",
    "docs/troubleshooting",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files - realistic but irrelevant or misleading
distractor_files = {
    "openclaw/config/bot_config.json": """{
  "bot_name": "CloudPaw",
  "version": "2.3.1",
  "language": "zh-CN",
  "telegram_token": "REDACTED",
  "privacy_mode": true,
  "default_reply_all": true
}
""",
    "openclaw/config/channel_config_OLD.json": """{
  "channel_id": "-100999888777",
  "channel_name": "OldChatRoom",
  "connected": false,
  "last_sync": "2024-01-15T08:23:11Z"
}
""",
    "openclaw/logs/session_2024_03_01.log": """[2024-03-01 10:23:11] Session started
[2024-03-01 10:23:15] Bot CloudPaw online
[2024-03-01 10:24:00] Received: /new
[2024-03-01 10:24:01] Session reset - rules cleared
[2024-03-01 10:24:05] WARNING: No AGENTS.md found, starting with default behavior
""",
    "openclaw/logs/session_2024_03_02.log": """[2024-03-02 09:10:05] Session started
[2024-03-02 09:10:10] Bot CloudPaw online
[2024-03-02 09:11:00] Channel message received from SunnyTail: hello
[2024-03-02 09:11:02] ERROR: Bot replied without name prefix - rule violation
""",
    "openclaw/plugins/anti_loop.py": """# Anti-loop plugin (stub)
# This plugin monitors for message loops
# Requires proper cooldown rules to be effective
LOOP_THRESHOLD = 5
LOOP_WINDOW_SECONDS = 60

def check_loop(message_history):
    pass  # implementation pending
""",
    "openclaw/sessions/active/current_session.json": """{
  "session_id": "sess_20240315_001",
  "start_time": "2024-03-15T14:00:00Z",
  "bot": "CloudPaw",
  "channel": null,
  "rules_loaded": false,
  "context_window": 5
}
""",
    "openclaw/sessions/archived/sess_20240201.json": """{
  "session_id": "sess_20240201_001",
  "rules_loaded": true,
  "rules_source": "inline",
  "note": "Rules were set inline but not persisted to AGENTS.md - lost on /new"
}
""",
    "openclaw/bots/cloudpaw/prompts/system_prompt_draft.txt": """You are CloudPaw, a friendly AI companion.
Be helpful and kind.
[DRAFT - not finalized]
TODO: Add channel interaction rules
TODO: Add message format rules
""",
    "openclaw/bots/cloudpaw/memory/long_term_memory.json": """{
  "owner": "Alice",
  "preferences": ["music", "cats", "technology"],
  "known_friends": ["Bob"],
  "friend_bots": ["SunnyTail"]
}
""",
    "openclaw/channels/channel_template.json": """{
  "_template": true,
  "channel_name": "REPLACE_ME",
  "channel_id": "REPLACE_ME",
  "bots": [],
  "rules_file": "AGENTS.md"
}
""",
    "telegram/bot_profiles/cloudpaw_profile.json": """{
  "username": "@CloudPawBot",
  "display_name": "CloudPaw",
  "privacy_mode": "disabled",
  "is_admin_in_channels": ["PawChat"]
}
""",
    "telegram/bot_profiles/sunnytail_profile.json": """{
  "username": "@SunnyTailBot",
  "display_name": "SunnyTail",
  "privacy_mode": "disabled",
  "is_admin_in_channels": ["PawChat"]
}
""",
    "telegram/webhooks/webhook_config.json": """{
  "endpoint": "https://openclaw.local/webhook",
  "secret_token": "REDACTED",
  "allowed_updates": ["channel_post", "edited_channel_post"]
}
""",
    "docs/setup/quickstart.txt": """OpenClaw Quick Setup Notes
===========================
1. Configure BotFather settings
2. Add bot as channel admin
3. Connect channel via Chat ID
4. Configure interaction rules
5. IMPORTANT: Save rules to AGENTS.md for persistence

See full documentation for rule format details.
""",
    "docs/troubleshooting/common_issues.txt": """Common Issues
=============
- Bot not responding: Check privacy mode setting
- Messages not visible: Ensure bot is channel admin
- Rules lost after /new command: Rules must be in AGENTS.md
- Infinite loop between bots: Missing cooldown rules
- Bot doesn't use name prefix: Check message format rules in AGENTS.md
""",
    "openclaw/data/exports/chat_export_20240310.json": """{
  "channel": "PawChat",
  "export_date": "2024-03-10",
  "message_count": 147,
  "participants": ["CloudPaw", "SunnyTail"],
  "loop_incidents": 3,
  "note": "3 loop incidents detected - no cooldown rules configured at time"
}
""",
    "openclaw/bots/cloudpaw/memory/channel_history.json": """{
  "PawChat": {
    "chat_id": "-100123456789",
    "joined": "2024-02-20",
    "last_active": "2024-03-10",
    "bot_is_admin": true
  }
}
""",
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# Create a deliberately WRONG / incomplete AGENTS.md stub to be fixed/replaced
wrong_agents_md = """# Bot Settings

Just be helpful and friendly.
Reply to everything.
"""

with open(os.path.join(workspace, "openclaw/bots/cloudpaw/AGENTS.md"), "w", encoding="utf-8") as f:
    f.write(wrong_agents_md)

print("Workspace initialized successfully.")
print("Files created:")
for filepath in distractor_files:
    print(f"  {workspace}/{filepath}")
print(f"  {workspace}/openclaw/bots/cloudpaw/AGENTS.md (stub - needs replacement)")