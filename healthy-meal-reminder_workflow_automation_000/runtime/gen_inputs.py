import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# Create deeply nested distractor directory structure
dirs = [
    "users/alice/profiles",
    "users/alice/history",
    "users/bob/profiles",
    "users/bob/history",
    "config/schedules/old",
    "config/schedules/archive",
    "config/reminders/deprecated",
    "logs/2024/01",
    "logs/2024/12",
    "scripts/utils",
    "scripts/legacy",
    "data/recipes/summer",
    "data/recipes/winter",
    "data/recipes/spring",
    "exports/weekly",
    "exports/monthly",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractors = {
    "users/alice/profiles/profile.json": json.dumps({
        "name": "Alice",
        "age": 28,
        "height_cm": 165,
        "weight_kg": 58,
        "mode": "增肌",
        "allergies": ["花生"],
        "timezone": "Asia/Shanghai"
    }, ensure_ascii=False, indent=2),
    "users/alice/history/2024-11-15.txt": "早餐: 燕麦粥\n午餐: 鸡胸肉沙拉\n晚餐: 蒸鱼",
    "users/bob/profiles/profile.json": json.dumps({
        "name": "Bob",
        "mode": "减肥",
        "timezone": "Asia/Tokyo"
    }, ensure_ascii=False, indent=2),
    "config/schedules/old/breakfast.cron": "0 8 * * * remind breakfast",
    "config/schedules/archive/legacy_schedule.txt": "OLD FORMAT - do not use\n8:00 breakfast\n12:00 lunch",
    "config/reminders/deprecated/old_reminders.json": json.dumps({
        "breakfast": "08:00",
        "lunch": "12:30",
        "dinner": "19:00"
    }),
    "logs/2024/01/intake_log.txt": "2024-01-10: 早餐 280kcal 午餐 450kcal 晚餐 300kcal",
    "logs/2024/12/intake_log.txt": "2024-12-05: 早餐 240kcal 午餐 500kcal 晚餐 350kcal",
    "scripts/utils/calorie_calc.py": "# Legacy calorie calculator\ndef calc(food): return 0",
    "scripts/legacy/old_cron_setup.sh": "#!/bin/bash\ncrontab -l > mycron\necho '0 8 * * * /usr/bin/python3 remind.py' >> mycron\ncrontab mycron",
    "data/recipes/summer/salads.txt": "凉面荞麦 380kcal\n清蒸鲈鱼 300kcal",
    "data/recipes/winter/soups.txt": "白萝卜炖牛腩 450kcal\n红枣枸杞乌鸡汤 320kcal",
    "data/recipes/spring/greens.txt": "荠菜豆腐汤 180kcal\n春笋炒肉 420kcal",
    "exports/weekly/week_2024_48.json": json.dumps({
        "week": 48,
        "avg_kcal": 1480,
        "days_on_track": 5
    }),
    "exports/monthly/november_2024_summary.txt": "November 2024: avg 1490 kcal/day, 22/30 days on target",
}
for rel_path, content in distractors.items():
    fpath = workspace / rel_path
    fpath.write_text(content, encoding="utf-8")

# The main task specification file (business requirements, NOT instructions)
task_spec = {
    "user": "Alice",
    "onboarding_date": "2024-12-10",
    "mode": "增肌",
    "timezone": "Asia/Shanghai",
    "request": (
        "请为用户 Alice 完成以下两项设置：\n"
        "1. 生成一个包含所有每日餐点提醒和跟进提醒及运动提醒和周报提醒的完整 openclaw cron 配置脚本文件，命名为 alice_cron_setup.sh。\n"
        "   - 用户处于增肌模式，时区 Asia/Shanghai。\n"
        "   - 需包含：早餐/午餐/晚餐/下午茶 的推荐提醒，以及对应的饭后30分钟跟进提醒，运动提醒，以及每周日的周报打卡提醒。\n"
        "   - cron 中的 message 参数需反映增肌模式（热量目标 2000-2500 kcal，强调蛋白质）。\n"
        "2. 生成用户 2024-12-10（冬季，周二）的一份示例饮食记录文件，命名为 diet_log_2024-12-10.md。\n"
        "   - 当天饮食：早餐选了A，午餐选了B，下午茶选了A（0kcal），晚餐选了C。\n"
        "   - 模式为增肌，目标热量 2000-2500 kcal。"
    )
}
(workspace / "task_spec.json").write_text(
    json.dumps(task_spec, ensure_ascii=False, indent=2), encoding="utf-8"
)

print("Workspace generated successfully.")
print(f"Files created: {len(list(workspace.rglob('*')))}")