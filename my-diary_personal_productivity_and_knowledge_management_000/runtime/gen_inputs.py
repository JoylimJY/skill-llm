import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# --- Create a deeply nested distractor directory structure ---

# Distractor: old notes app data
old_notes_dir = workspace / "legacy_notes" / "2024" / "archive"
old_notes_dir.mkdir(parents=True, exist_ok=True)

# Distractor: an old, WRONG-FORMAT diary file (flat array, no version, wrong ID type)
old_diary_wrong = {
    "entries": [
        {"id": 1, "text": "This is an old note format", "date": "2024-01-10"},
        {"id": 2, "text": "Another old note", "date": "2024-01-11"}
    ]
}
with open(old_notes_dir / "notes_backup.json", "w", encoding="utf-8") as f:
    json.dump(old_diary_wrong, f, ensure_ascii=False, indent=2)

# Distractor: a partial diary with wrong schema (missing 'version', entries as root array)
wrong_schema_diary = [
    {"id": "abc123", "content": "Flat array diary entry", "created_at": "2025-01-01 10:00:00"}
]
with open(workspace / "legacy_notes" / "old_diary.json", "w", encoding="utf-8") as f:
    json.dump(wrong_schema_diary, f, ensure_ascii=False, indent=2)

# Distractor: some config files
config_dir = workspace / "config"
config_dir.mkdir(parents=True, exist_ok=True)

app_config = {"app_name": "DiaryApp", "version": "2.0", "storage": "/tmp/diaries"}
with open(config_dir / "app_config.json", "w") as f:
    json.dump(app_config, f, indent=2)

settings = {"theme": "dark", "language": "zh-CN", "auto_backup": True}
with open(config_dir / "settings.json", "w") as f:
    json.dump(settings, f, indent=2)

# Distractor: logs directory
logs_dir = workspace / "logs" / "2025"
logs_dir.mkdir(parents=True, exist_ok=True)

with open(logs_dir / "app.log", "w") as f:
    f.write("2025-01-01 08:00:00 INFO Application started\n")
    f.write("2025-01-01 08:01:00 INFO Diary loaded\n")
    f.write("2025-03-15 09:30:00 ERROR Failed to write diary entry\n")
    f.write("2025-03-16 10:00:00 INFO Backup completed\n")

with open(logs_dir / "error.log", "w") as f:
    f.write("2025-03-15 09:30:00 ERROR FileNotFoundError: diary.json not found\n")

# Distractor: temp files
temp_dir = workspace / "tmp" / "cache"
temp_dir.mkdir(parents=True, exist_ok=True)

with open(temp_dir / "draft_001.txt", "w", encoding="utf-8") as f:
    f.write("今天天气很好，我想出去走走。(draft, not saved)\n")

with open(temp_dir / "draft_002.txt", "w", encoding="utf-8") as f:
    f.write("学习了新的编程技巧。(draft, not saved)\n")

# Distractor: a totally different JSON with 'version' key (to confuse)
with open(config_dir / "schema_v1.json", "w") as f:
    json.dump({"version": "1.0", "type": "config", "fields": ["name", "age"]}, f, indent=2)

# Distractor: a markdown file with diary-like content but wrong format
with open(workspace / "legacy_notes" / "diary_notes.md", "w", encoding="utf-8") as f:
    f.write("# Old Diary Notes\n\n")
    f.write("## 2024-12-01\n今天工作很顺利。\n\n")
    f.write("## 2024-12-02\n感觉有点累，需要休息。\n")

# Distractor: user profile (not diary)
user_dir = workspace / "user"
user_dir.mkdir(parents=True, exist_ok=True)

with open(user_dir / "profile.json", "w", encoding="utf-8") as f:
    json.dump({"name": "Nancy", "email": "nancy@example.com", "joined": "2024-01-01"}, f, indent=2)

with open(user_dir / "preferences.txt", "w", encoding="utf-8") as f:
    f.write("preferred_language=zh\nnotifications=on\nbackup_frequency=daily\n")

# Distractor: a malformed JSON file (syntax error) to test error resilience
with open(workspace / "legacy_notes" / "corrupted.json", "w") as f:
    f.write('{"entries": [{"id": "bad", "content": "broken json",}]}')  # trailing comma = invalid

# Create the diary directory (as per skill path convention) but leave it EMPTY
# to ensure the agent creates the file from scratch
diary_dir = workspace / "diary"
diary_dir.mkdir(parents=True, exist_ok=True)
# Leave a README-style placeholder that gives no hints about schema
with open(diary_dir / ".gitkeep", "w") as f:
    f.write("")

print("Workspace generated successfully.")
print(f"Structure:")
for p in sorted(workspace.rglob("*")):
    print(f"  {p.relative_to(workspace)}")