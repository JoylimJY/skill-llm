import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# --- Deep distractor directory structure ---
dirs = [
    "logs/2024/jan",
    "logs/2024/feb",
    "config/telegram",
    "config/notifications",
    "users/founder",
    "users/assistant",
    "reports/weekly",
    "reports/monthly",
    "templates/buttons",
    "templates/messages",
    "archive/old_configs",
    "archive/deprecated",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
(workspace / "logs/2024/jan/session_log.txt").write_text(
    "2024-01-15 09:12:33 - User connected\n2024-01-15 09:13:00 - Message sent\n"
)
(workspace / "logs/2024/feb/session_log.txt").write_text(
    "2024-02-10 14:05:22 - Reconnect event\n2024-02-10 14:06:01 - Heartbeat OK\n"
)
(workspace / "config/telegram/bot_config.json").write_text(json.dumps({
    "bot_name": "FounderAssistBot",
    "token": "REDACTED",
    "polling_interval": 500
}, indent=2))
(workspace / "config/notifications/push_settings.json").write_text(json.dumps({
    "quiet_hours_start": "23:00",
    "quiet_hours_end": "07:00",
    "channels": ["telegram", "email"]
}, indent=2))
(workspace / "users/founder/profile.json").write_text(json.dumps({
    "user_id": "FOUNDER_001",
    "name": "Alex Chen",
    "timezone": "Asia/Shanghai",
    "role": "CEO"
}, indent=2))
(workspace / "users/assistant/capabilities.json").write_text(json.dumps({
    "skills": ["scheduling", "research", "reporting"],
    "model": "gpt-4o"
}, indent=2))
(workspace / "reports/weekly/week_summary.txt").write_text(
    "Week of 2024-06-10: 12 tasks completed, 3 pending, 1 escalation.\n"
)
(workspace / "reports/monthly/june_2024.txt").write_text(
    "Monthly report: Revenue up 8%. Team capacity at 87%.\n"
)

# Outdated/wrong button template (distractor - uses wrong structure)
(workspace / "templates/buttons/old_button_schema.json").write_text(json.dumps({
    "buttons": [
        {"label": "Check Status", "action": "status_check"},
        {"label": "Manual", "action": "manual"}
    ]
}, indent=2))

# Wrong flat-list button template (distractor)
(workspace / "templates/buttons/flat_buttons_DEPRECATED.json").write_text(json.dumps([
    {"text": "Morning Brief", "data": "morning_brief"},
    {"text": "Manual Input", "data": "manual"}
], indent=2))

(workspace / "templates/messages/greeting_template.txt").write_text(
    "Good {time_of_day}, {user_name}! Here's your update.\n"
)
(workspace / "archive/old_configs/v1_button_config.json").write_text(json.dumps({
    "version": "1.0",
    "note": "DEPRECATED - do not use",
    "buttons": {"morning": ["brief", "commute"], "evening": ["recap", "home"]}
}, indent=2))
(workspace / "archive/deprecated/legacy_cta.txt").write_text(
    "Legacy CTA format: Use inline keyboard markup with reply_markup field.\n"
)

# --- THE ACTUAL TASK INPUT ---
# A conversation log representing an administrative/planning session
# happening in the AFTERNOON / WRAP-UP window (we fix time to 16:30 for determinism)
# The agent must produce the bot's response payload as bot_response.json

conversation_log = {
    "session_id": "sess_20240612_1630",
    "simulated_time": "16:30",
    "user_id": "FOUNDER_001",
    "conversation": [
        {
            "role": "user",
            "timestamp": "16:28:05",
            "content": "Can you help me draft the board meeting agenda for next quarter? I also need to pull last quarter's budget data."
        },
        {
            "role": "assistant",
            "timestamp": "16:29:10",
            "content": "Sure! I've started drafting the agenda and I'm pulling the budget figures now. I'll have a summary ready shortly."
        },
        {
            "role": "user",
            "timestamp": "16:29:55",
            "content": "Great, also remind me to send the pre-read docs to investors before EOD."
        },
        {
            "role": "assistant",
            "timestamp": "16:30:00",
            "content": "Noted! I've set a reminder. Your documents are being prepared."
        }
    ],
    "task_just_completed": True,
    "task_type": "administrative_planning",
    "bot_reply_text": "I've prepared the board meeting agenda draft and gathered last quarter's budget data. Reminder set for investor pre-reads. What would you like to do next?"
}

(workspace / "conversation_log.json").write_text(json.dumps(conversation_log, indent=2))

# Instruction file for the agent describing the business goal
task_brief = """# Task Brief

You are operating as the AI backbone of FounderAssistBot, a personal productivity assistant for startup founders on Telegram.

A session has just completed (see: conversation_log.json). The assistant has finished helping the founder with an administrative/planning task during the afternoon.

Your job is to produce the final outgoing bot message payload that FounderAssistBot will send. This payload must be saved as `bot_response.json` in the workspace root.

The payload represents what the bot would transmit — it must include:
- The reply text (use the `bot_reply_text` field from the conversation log as the message body)
- The appropriate interactive quick-action options for the user, contextually suited to both the time of day and the nature of the task just completed

The `simulated_time` field in the conversation log tells you what time it is. Use it to select the right set of options.

Refer to the skill documentation in the workspace to understand the exact payload structure and the precise option values required.
"""

(workspace / "TASK_BRIEF.md").write_text(task_brief)

# Place SKILL.md and time_logic.md as the agent's reference docs
skill_md = Path("/workspace/SKILL.md")
skill_md.write_text("""---
name: telegram-smart-launcher
description: Enhance Telegram replies with context-aware dynamic CTA buttons (Smart Launcher UI). Use when replying to users on Telegram to provide relevant, time-sensitive, and task-oriented options for better interaction.
---

# Telegram Smart Launcher (Smart Launcher UI)

This skill enables the agent to provide an interactive and efficient user experience on Telegram by appending context-aware CTA (Call to Action) buttons to replies.

## Usage Guidelines

When responding to a user on Telegram, always consider if providing quick-action buttons would improve efficiency.

### Button Selection Logic

1.  **Time of Day Awareness**:
    - **Morning (07:00 - 10:00)**: Focus on daily briefings, commute status, and agenda checks.
    - **Work Hours (10:00 - 16:00)**: Focus on task progress, deep research, and project-specific actions.
    - **Wrap-up (16:00 - 18:00)**: Focus on daily recaps, route home status, and tomorrow's preparation.
    - **Night (20:00 - 23:00)**: Focus on reflection, mood checks, and planning for the next day.

2.  **Context Awareness**:
    - If the user is working on administrative or planning tasks, offer buttons for document drafting or data lookup.
    - If the user is working on creative or design tasks, offer buttons for tool links or asset management.
    - If a task just finished, offer "Next Steps" or "Recap" buttons.

3.  **The "Free Text" Fallback**:
    - Always include an option for free text input (e.g., "⌨️ Manual Input") to ensure the user feels in control.

## Implementation Pattern

Use the `message` tool with the `buttons` parameter. The `buttons` array is an array of arrays (rows) of button objects `[{text, callback_data}]`.

### Example (Wrap-up Phase)

```javascript
message({
  action: "send",
  target: "USER_ID",
  message: "I've prepared the daily report for you.",
  buttons: [
    [
      { text: "📝 Daily Recap", callback_data: "/update" },
      { text: "🏠 Route Home", callback_data: "Check route home" }
    ],
    [
      { text: "⏭️ Tomorrow's Agenda", callback_data: "What is the agenda for tomorrow?" },
      { text: "⌨️ Manual Input", callback_data: "keyboard_manual" }
    ]
  ]
})
```

## References

- See [references/time_logic.md](references/time_logic.md) for detailed time-based button presets.
""")

refs_dir = workspace / "references"
refs_dir.mkdir(exist_ok=True)

(refs_dir / "time_logic.md").write_text("""# Time-Based Button Presets

Use these presets based on the current system time.

## Morning (07:00 - 10:00)
- `[{"text": "☀️ Morning Briefing", "callback_data": "/update"}, {"text": "🚗 Commute Status", "callback_data": "Check commute"}]`
- `[{"text": "📅 Today's Agenda", "callback_data": "What is the agenda for today?"}, {"text": "⌨️ Manual Input", "callback_data": "keyboard_manual"}]`

## Mid-Day (10:00 - 15:00)
- `[{"text": "🔬 Deep Research", "callback_data": "Help me research a topic"}, {"text": "📊 Progress Check", "callback_data": "/status"}]`
- `[{"text": "💡 Quick Tip", "callback_data": "Give me a productivity tip"}, {"text": "⌨️ Manual Input", "callback_data": "keyboard_manual"}]`

## Afternoon / Wrap-up (15:00 - 18:00)
- `[{"text": "⏮️ Daily Recap", "callback_data": "/update"}, {"text": "🏠 Route Home", "callback_data": "Check route home"}]`
- `[{"text": "⏭️ Tomorrow's Agenda", "callback_data": "What is the agenda for tomorrow?"}, {"text": "⌨️ Manual Input", "callback_data": "keyboard_manual"}]`

## Night (20:00 - 23:00)
- `[{"text": "🌙 Night Reflection", "callback_data": "Help me reflect on today"}, {"text": "📝 Note Idea", "callback_data": "I want to note an idea for tomorrow"}]`
- `[{"text": "🔕 Do Not Disturb", "callback_data": "Turn off notifications until morning"}, {"text": "⌨️ Manual Input", "callback_data": "keyboard_manual"}]`
""")

print("Workspace generated successfully.")
print(f"Files created: {list(workspace.rglob('*'))}")