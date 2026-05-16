import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── 1. Simulate the skill directory structure ──────────────────────────────
skill_dir = workspace / "skills" / "lunar-reminder"
skill_data_dir = skill_dir / "data"
skill_data_dir.mkdir(parents=True, exist_ok=True)

# Install lunar-javascript inside the skill directory (node_modules)
node_modules = skill_dir / "node_modules"
node_modules.mkdir(parents=True, exist_ok=True)

# ── 2. Create distractor files ─────────────────────────────────────────────
# Distractor: a fake events file with wrong schema in a sibling directory
other_skill = workspace / "skills" / "solar-reminder" / "data"
other_skill.mkdir(parents=True, exist_ok=True)
(other_skill / "events.json").write_text(json.dumps([
    {"title": "New Year", "month": 1, "day": 1}
], ensure_ascii=False, indent=2))

# Distractor: old backup
backup_dir = workspace / "skills" / "lunar-reminder" / "backup"
backup_dir.mkdir(parents=True, exist_ok=True)
(backup_dir / "events.bak.json").write_text(json.dumps([
    {"name": "旧事件", "lunarMonth": 1, "lunarDay": 1}
], ensure_ascii=False, indent=2))

# Distractor: a config file for something unrelated
(workspace / "skills" / "lunar-reminder" / "config.yaml").write_text(
    "timezone: Asia/Shanghai\ndefault_advance: 3\n"
)

# Distractor: a README-like file but in Chinese about a different tool
(workspace / "skills" / "lunar-reminder" / "NOTES.txt").write_text(
    "注意：此目录为lunar-reminder技能目录。node_modules由包管理器维护，请勿手动删除。\n"
    "旧版数据格式已废弃，请以data/events.json为准。\n"
)

# Distractor: package stubs
(skill_dir / "package.json").write_text(json.dumps({
    "name": "lunar-reminder",
    "version": "1.0.0",
    "dependencies": {"lunar-javascript": "^1.0.0"}
}, indent=2))

# More distractors: unrelated scripts
scripts_dir = workspace / "scripts"
scripts_dir.mkdir(parents=True, exist_ok=True)
(scripts_dir / "sync_calendar.sh").write_text("#!/bin/bash\necho 'Legacy calendar sync'\n")
(scripts_dir / "convert_dates.py").write_text("# Old date conversion script (deprecated)\nimport datetime\n")

logs_dir = workspace / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)
for i in range(4):
    (logs_dir / f"app_{i}.log").write_text(f"[INFO] Log entry {i}\n")

# Distractor: a partial events.json that already has ONE event (not duplicating what agent needs to add)
# This event is unrelated to the task events
existing_events = [
    {
        "name": "爷爷生日",
        "lunarMonth": 9,
        "lunarDay": 15,
        "lunarMonthName": "九月",
        "lunarDayName": "十五",
        "advanceDays": 2,
        "reminderTime": "09:00",
        "note": "别忘了买蛋糕",
        "createdAt": "2025-01-01T00:00:00.000Z"
    }
]
(skill_data_dir / "events.json").write_text(
    json.dumps(existing_events, ensure_ascii=False, indent=2)
)

# ── 3. Create the openclaw mock ─────────────────────────────────────────────
mock_dir = workspace / "mock_bin"
mock_dir.mkdir(parents=True, exist_ok=True)

openclaw_script = mock_dir / "openclaw"
openclaw_script.write_text("""#!/usr/bin/env python3
import sys
import json
import os
from pathlib import Path

CRON_LOG = Path("/workspace/cron_operations.json")

def load_log():
    if CRON_LOG.exists():
        return json.loads(CRON_LOG.read_text())
    return []

def save_log(ops):
    CRON_LOG.write_text(json.dumps(ops, ensure_ascii=False, indent=2))

args = sys.argv[1:]

if not args:
    print("openclaw: no command")
    sys.exit(1)

if args[0] == "cron":
    ops = load_log()
    if args[1] == "rm":
        task_name = args[2]
        ops.append({"op": "rm", "name": task_name})
        save_log(ops)
        print(f"Removed cron task: {task_name}")
    elif args[1] == "add":
        # parse --name --cron --message --tz
        task = {"op": "add"}
        i = 2
        while i < len(args):
            if args[i] == "--name":
                task["name"] = args[i+1]; i += 2
            elif args[i] == "--cron":
                task["cron"] = args[i+1]; i += 2
            elif args[i] == "--message":
                task["message"] = args[i+1]; i += 2
            elif args[i] == "--tz":
                task["tz"] = args[i+1]; i += 2
            else:
                i += 1
        ops.append(task)
        save_log(ops)
        print(f"Added cron task: {task.get('name')}")
    else:
        print(f"Unknown cron subcommand: {args[1]}")
else:
    print(f"Unknown command: {args[0]}")
""")
openclaw_script.chmod(0o755)

# ── 4. Write the task description file ────────────────────────────────────
(workspace / "task_context.txt").write_text(
    "任务上下文：\n"
    "需要添加两个农历提醒，然后同步到定时任务系统。\n"
    "事件1：奶奶生日，腊月廿三，提前2天提醒\n"
    "事件2：元宵节，正月十五，提前1天提醒\n"
    "添加完毕后请同步所有农历提醒到定时任务。\n"
    "（技能目录位于 /workspace/skills/lunar-reminder）\n",
    encoding="utf-8"
)

print("Workspace generated successfully.")
print(f"Skill dir: {skill_dir}")
print(f"Events file: {skill_data_dir / 'events.json'}")