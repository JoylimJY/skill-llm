#!/usr/bin/env python3
"""
Generate the sandbox workspace for the member-manager evaluation task.
"""
import os
import json
import stat
import random

random.seed(42)

workspace = "/workspace"

# ── 1. OpenClaw config skeleton (session.json with a specific user_id) ──────
openclaw_dir = os.path.expanduser("~/.openclaw")
os.makedirs(openclaw_dir, exist_ok=True)

session_data = {
    "version": "1.0",
    "user_id": "telegram_88291047",
    "locale": "zh-TW",
    "timezone": "Asia/Taipei"
}
with open(os.path.join(openclaw_dir, "session.json"), "w") as f:
    json.dump(session_data, f, ensure_ascii=False, indent=2)

# ── 2. Workspace distractor structure (10+ distractor files) ─────────────────
dirs = [
    f"{workspace}/logs",
    f"{workspace}/archive/2023",
    f"{workspace}/archive/2024",
    f"{workspace}/tmp",
    f"{workspace}/config",
    f"{workspace}/exports",
    f"{workspace}/exports/csv",
    f"{workspace}/backups",
    f"{workspace}/scripts",
    f"{workspace}/notes",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

distractors = {
    f"{workspace}/logs/app.log": "2024-12-01 INFO member-manager started\n2024-12-01 ERROR failed to connect\n",
    f"{workspace}/logs/error.log": "Error: undefined session\nError: path not found\n",
    f"{workspace}/archive/2023/members_backup.json": json.dumps([
        {"name": "舊資料", "group": "廢棄", "id": "old-001"}
    ], ensure_ascii=False),
    f"{workspace}/archive/2024/reminders_backup.json": json.dumps([], ensure_ascii=False),
    f"{workspace}/tmp/scratch.txt": "temp data - ignore\n",
    f"{workspace}/config/app_config.yaml": "debug: false\nlog_level: info\nmax_members: 500\n",
    f"{workspace}/config/legacy_settings.json": json.dumps({
        "session_key": "OLD_KEY_DO_NOT_USE",
        "data_path": "/old/path/members.json"
    }),
    f"{workspace}/exports/csv/contacts_export.csv": "name,phone,birthday\n張三,0912345678,1980-01-01\n",
    f"{workspace}/exports/all_members_20241201.json": json.dumps([
        {"name": "過時資料", "group": "家庭", "birthday_solar": "1980-01-01"}
    ], ensure_ascii=False),
    f"{workspace}/backups/members_20240101.json": json.dumps([], ensure_ascii=False),
    f"{workspace}/scripts/migrate.py": "# Migration script - do not use\nprint('migrating...')\n",
    f"{workspace}/notes/todo.txt": "- Update phone numbers\n- Add new members\n- Check reminders\n",
}
for path, content in distractors.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# ── 3. Pre-populate a WRONG/INCOMPLETE members.json for the default session ──
# (this is a trap: agent must use the session key from session.json, not "default")
default_user_dir = os.path.expanduser("~/.openclaw/workspace/users/default")
os.makedirs(default_user_dir, exist_ok=True)
with open(os.path.join(default_user_dir, "members.json"), "w") as f:
    json.dump([
        {
            "id": "decoy-0001",
            "name": "陷阱成員",
            "group": "家庭",
            "relationship": "陷阱",
            "phone": "",
            "birthday_solar": None,
            "birthday_lunar": {"month": 1, "day": 1, "is_leap_month": False},
            "birthday_lunar_solar_this_year": None,
            "anniversaries": [],
            "notes": "This is the WRONG user directory - agent should use telegram_88291047",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    ], f, ensure_ascii=False, indent=2)
with open(os.path.join(default_user_dir, "reminders.json"), "w") as f:
    json.dump([], f, ensure_ascii=False)

# ── 4. The correct user directory starts EMPTY (agent must create and populate) ──
correct_user_dir = os.path.expanduser("~/.openclaw/workspace/users/telegram_88291047")
os.makedirs(correct_user_dir, exist_ok=True)
# Do NOT pre-create members.json here — agent must initialize it

print("Sandbox workspace generated successfully.")
print(f"Session user_id: telegram_88291047")
print(f"Correct data path: {correct_user_dir}")