import os
import random
from pathlib import Path

random.seed(42)

# --- Define workspace root ---
workspace = Path("/home/user/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# --- Create the skill directory structure (mimicking ~/.openclaw) ---
skill_root = workspace / ".openclaw" / "workspace" / "skills" / "diet-logger"
scripts_dir = skill_root / "scripts"
scripts_dir.mkdir(parents=True, exist_ok=True)

# --- Create the actual log_diet.py script ---
log_diet_script = scripts_dir / "log_diet.py"
log_diet_script.write_text(
    '''\
#!/usr/bin/env python3
"""饮食记录脚本 - 将饮食数据保存到 Obsidian 库"""

import argparse
import os
from datetime import datetime
from pathlib import Path

SAVE_DIR = "/mnt/c/Users/loong/iCloudDrive/iCloud~md~obsidian/HomeMo.Art/05-Daily/"
MEAL_ORDER = ["早饭", "中饭", "晚饭", "加餐"]


def get_or_create_record(date_str: str) -> dict:
    """读取现有记录或创建新记录"""
    filepath = Path(SAVE_DIR) / f"饮食记录-{date_str}.md"
    record = {meal: [] for meal in MEAL_ORDER}
    record["_record_time"] = None

    if filepath.exists():
        current_meal = None
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line_stripped = line.rstrip("\\n")
                for meal in MEAL_ORDER:
                    if line_stripped == f"## {meal}":
                        current_meal = meal
                        break
                else:
                    if current_meal and line_stripped.startswith("- "):
                        record[current_meal].append(line_stripped[2:])
    return record


def format_record(date_str: str, record: dict, record_time: str) -> str:
    """格式化饮食记录为 Markdown"""
    lines = [f"# {date_str} 饮食记录", ""]
    for meal in MEAL_ORDER:
        lines.append(f"## {meal}")
        for item in record[meal]:
            lines.append(f"- {item}")
        lines.append("")
    lines.append("---")
    lines.append(f"*记录时间: {record_time}*")
    lines.append("")
    return "\\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="记录饮食")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"),
                        help="日期 (YYYY-MM-DD)")
    parser.add_argument("--meal", required=True,
                        choices=["早饭", "中饭", "晚饭", "加餐"],
                        help="餐段")
    parser.add_argument("--items", required=True,
                        help="食物列表，逗号分隔")
    args = parser.parse_args()

    items = [i.strip() for i in args.items.split(",") if i.strip()]

    Path(SAVE_DIR).mkdir(parents=True, exist_ok=True)

    record = get_or_create_record(args.date)
    record[args.meal] = items

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    content = format_record(args.date, record, now_str)

    filepath = Path(SAVE_DIR) / f"饮食记录-{args.date}.md"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ 已记录 {args.date} {args.meal}: {', '.join(items)}")
    print(f"📁 文件: {filepath}")


if __name__ == "__main__":
    main()
''',
    encoding="utf-8",
)
log_diet_script.chmod(0o755)

# --- Create the Obsidian save directory (simulated on local FS) ---
obsidian_dir = Path("/mnt/c/Users/loong/iCloudDrive/iCloud~md~obsidian/HomeMo.Art/05-Daily")
obsidian_dir.mkdir(parents=True, exist_ok=True)

# --- Pre-populate the save dir with distractor files (unrelated entries) ---
distractors = [
    ("饮食记录-2026-03-20.md", "# 2026-03-20 饮食记录\n\n## 早饭\n- 豆浆\n- 油条\n\n## 中饭\n- 盒饭\n\n## 晚饭\n- 炒饭\n\n## 加餐\n\n---\n*记录时间: 2026-03-20 21:00*\n"),
    ("饮食记录-2026-03-21.md", "# 2026-03-21 饮食记录\n\n## 早饭\n- 面包\n\n## 中饭\n\n## 晚饭\n- 火锅\n\n## 加餐\n- 坚果\n\n---\n*记录时间: 2026-03-21 20:30*\n"),
    ("日记-2026-03-22.md", "# 2026-03-22\n今天天气不错。\n"),
    ("健身记录-2026-03-23.md", "# 健身\n- 跑步 5km\n- 俯卧撑 50个\n"),
    ("体重记录.md", "| 日期 | 体重 |\n|------|------|\n| 2026-03-20 | 68kg |\n"),
]
for fname, content in distractors:
    (obsidian_dir / fname).write_text(content, encoding="utf-8")

# --- Create extra distractor files in workspace ---
notes_dir = workspace / "notes"
notes_dir.mkdir(exist_ok=True)
(notes_dir / "todo.md").write_text("# TODO\n- 买菜\n- 健身\n", encoding="utf-8")
(notes_dir / "shopping_list.txt").write_text("鸡蛋\n牛奶\n苹果\n西兰花\n", encoding="utf-8")

config_dir = workspace / ".openclaw" / "config"
config_dir.mkdir(parents=True, exist_ok=True)
(config_dir / "settings.json").write_text('{"theme": "dark", "language": "zh-CN"}\n', encoding="utf-8")

skills_index = workspace / ".openclaw" / "workspace" / "skills" / "index.json"
skills_index.write_text(
    '[\n  {"name": "diet-logger", "version": "1.0.0"},\n  {"name": "workout-logger", "version": "0.9.0"}\n]\n',
    encoding="utf-8",
)

logs_dir = workspace / ".openclaw" / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)
(logs_dir / "agent.log").write_text("[INFO] Agent started.\n[INFO] Skill loaded: diet-logger\n", encoding="utf-8")

templates_dir = workspace / ".openclaw" / "workspace" / "skills" / "diet-logger" / "templates"
templates_dir.mkdir(exist_ok=True)
(templates_dir / "weekly_summary.md").write_text("# 周饮食总结模板\n（每周自动生成）\n", encoding="utf-8")

archive_dir = obsidian_dir / "archive"
archive_dir.mkdir(exist_ok=True)
(archive_dir / "饮食记录-2026-02-14.md").write_text(
    "# 2026-02-14 饮食记录\n\n## 早饭\n- 汤圆\n\n## 中饭\n- 年夜饭\n\n## 晚饭\n- 饺子\n\n## 加餐\n\n---\n*记录时间: 2026-02-14 22:00*\n",
    encoding="utf-8",
)

print("✅ Workspace initialized successfully.")
print(f"   Skill script: {log_diet_script}")
print(f"   Obsidian dir: {obsidian_dir}")