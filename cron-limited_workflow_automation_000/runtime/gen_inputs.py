#!/usr/bin/env python3
import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# Create realistic distractor directory structure
dirs = [
    "reminders/drafts",
    "reminders/archive",
    "config/legacy",
    "config/templates",
    "scripts/utils",
    "scripts/deprecated",
    "data/contacts",
    "data/exports",
    "logs/2023",
    "logs/2024",
    "docs/internal",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "reminders/drafts/draft_reminder.txt": "TODO: send birthday msg to team\nDate: TBD\nChannel: wechat",
    "reminders/archive/old_cron.txt": "*/5 * * * * /usr/bin/python3 /scripts/send_msg.py",
    "config/legacy/cron_config_v1.json": json.dumps({
        "tasks": [
            {"id": "abc123", "interval": "5m", "count": 10, "msg": "old format reminder"}
        ]
    }, indent=2),
    "config/templates/weixin_template.json": json.dumps({
        "channel": "openclaw-weixin",
        "to": "placeholder@im.wechat",
        "message_template": "{name} 你好！"
    }, indent=2),
    "scripts/utils/lunar_convert.py": "# Old conversion script - DEPRECATED\n# Use lunarcalendar library instead\ndef old_convert(month, day):\n    pass\n",
    "scripts/deprecated/send_wechat.sh": "#!/bin/bash\n# Deprecated: use openclaw CLI\ncurl -X POST http://old-api/send -d '{}'",
    "data/contacts/team_contacts.json": json.dumps([
        {"name": "Alice", "wechat": "alice@im.wechat", "lunar_birthday": "3-22"},
        {"name": "Bob", "wechat": "bob@im.wechat", "lunar_birthday": "7-20"},
        {"name": "Charlie", "wechat": "charlie@im.wechat", "lunar_birthday": "11-5"},
    ], indent=2),
    "data/exports/schedule_export.csv": "id,type,schedule,status\n1,once,2024-01-01 08:00,done\n2,repeat,every 5m,expired\n3,lunar,8-15,active",
    "logs/2023/cron_errors.log": "[ERROR] 2023-08-15 Task not found\n[ERROR] 2023-09-01 Channel unavailable",
    "logs/2024/cron_run.log": "[INFO] 2024-07-01 Daily check triggered\n[INFO] 2024-07-02 No reminders today",
    "docs/internal/system_notes.md": "# System Notes\n- Cron jobs managed via openclaw CLI\n- Lunar calendar support added in v2\n- Contact: devops@company.com",
    "scripts/utils/date_helper.py": "from datetime import date, timedelta\n\ndef days_until(target):\n    today = date.today()\n    delta = target - today\n    return delta.days\n",
}

for rel_path, content in distractor_files.items():
    fpath = workspace / rel_path
    fpath.write_text(content, encoding="utf-8")

# Create a task specification file that the agent must read to understand requirements
task_spec = {
    "task": "Setup automated reminder system",
    "requirements": [
        {
            "id": "task_a",
            "description": "Water drinking reminder: every 4 minutes, 5 times total, then auto-stop",
            "message": "💧 时间到了，记得喝水！保持健康！",
            "channel": "openclaw-weixin",
            "to": "user-abc123@im.wechat"
        },
        {
            "id": "task_b",
            "description": "Lunar birthday reminder for Bob: lunar 7th month, 20th day, remind 2 days early, yearly, at 09:30",
            "message": "🎂 Bob的生日快到了，记得准备礼物！",
            "channel": "openclaw-weixin",
            "to": "manager-xyz@im.wechat",
            "lunar_month": 7,
            "lunar_day": 20,
            "days_before": 2,
            "time": "09:30",
            "yearly": True
        },
        {
            "id": "task_c",
            "description": "Simulate daily check: given today is the reminder day for Bob's birthday (2 days before the 2025 solar date of lunar 7-20), output the correct openclaw agent command",
            "note": "Write a Python script named 'daily_check_sim.py' in /workspace that simulates receiving CRON-LIMITED-DAILY-CHECK for the bob birthday config and executes the correct openclaw agent command. The script must compute today's date as the reminder date (2 days before lunar 7-20 of 2025 converted to solar), then invoke the openclaw agent command."
        }
    ]
}
(workspace / "task_spec.json").write_text(json.dumps(task_spec, indent=2, ensure_ascii=False), encoding="utf-8")

# Pre-compute the expected solar date for lunar 7-20, 2025 (for the eval script to verify)
# We'll do this in the eval script using lunarcalendar

print("Workspace generated successfully.")
print(f"Files created: {list(workspace.rglob('*'))}")