import os
import random
import stat

random.seed(42)

# --- Define base paths ---
workspace = "/workspace"
skill_base = os.path.join(workspace, ".openclaw/workspace/skills/mood-logger")
scripts_dir = os.path.join(skill_base, "scripts")
obsidian_dir = os.path.join(workspace, "obsidian_vault/05-Daily")
distractor_base = os.path.join(workspace, "personal_notes")

os.makedirs(scripts_dir, exist_ok=True)
os.makedirs(obsidian_dir, exist_ok=True)
os.makedirs(distractor_base, exist_ok=True)

# --- Create distractor files ---
distractor_files = [
    ("personal_notes/journal_2025_01.txt", "January reflections. Had a good start to the year."),
    ("personal_notes/todo_list.md", "# TODO\n- [ ] Buy groceries\n- [ ] Call dentist\n- [ ] Read book"),
    ("personal_notes/health_tracker.csv", "date,steps,calories\n2025-07-01,8000,2100\n2025-07-02,6500,1900"),
    ("personal_notes/archive/old_diary_2024.txt", "Old diary entry from 2024. Things were different then."),
    ("personal_notes/archive/expenses_june.csv", "item,cost\ncoffee,4.5\nlunch,12.0"),
    ("personal_notes/templates/weekly_review_template.md", "# Weekly Review\n## Wins\n## Challenges\n## Next Week"),
    ("personal_notes/templates/habit_tracker.md", "# Habit Tracker\n| Habit | Mon | Tue | Wed |\n|-------|-----|-----|-----|"),
    ("personal_notes/reading_list.txt", "1. Atomic Habits\n2. Deep Work\n3. The Pragmatic Programmer"),
    ("personal_notes/contacts.json", '{"emergency": "555-0100", "doctor": "555-0199"}'),
    ("personal_notes/goals_2025.md", "# 2025 Goals\n1. Exercise 3x/week\n2. Read 12 books\n3. Learn a new skill"),
    ("personal_notes/archive/mood_notes_old.txt", "Rough notes: felt ok monday, stressed tuesday, better friday"),
    ("personal_notes/config_backup.yaml", "theme: dark\nfont_size: 14\nlanguage: zh-CN"),
]

for rel_path, content in distractor_files:
    full_path = os.path.join(workspace, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# --- Write log_mood.py ---
# This is the real script that the SKILL.md refers to.
# It saves to the HARDCODED path from SKILL.md (will be patched in setup_script).
log_mood_script = r'''#!/usr/bin/env python3
"""Mood logger script for Obsidian vault."""
import argparse
import os
import re
from datetime import datetime

SAVE_DIR = "/mnt/c/Users/loong/iCloudDrive/iCloud~md~obsidian/HomeMo.Art/05-Daily"

EMOJI_MAP = [
    (9, 10, "😄"),
    (7, 8,  "😊"),
    (5, 6,  "😐"),
    (3, 4,  "😔"),
    (1, 2,  "😢"),
]

def get_emoji(score):
    for low, high, emoji in EMOJI_MAP:
        if low <= score <= high:
            return emoji
    return "😐"

def parse_existing_entries(content):
    """Parse existing mood entries from file content."""
    entries = []
    # Match entry blocks
    pattern = re.compile(
        r'### (.+?) 评分: (\d+)/10\n\n\*\*标签\*\*: (.+?)\n(?:\n\*\*备注\*\*: (.+?)\n)?',
        re.DOTALL
    )
    for m in pattern.finditer(content):
        entries.append({
            'emoji': m.group(1).strip(),
            'score': int(m.group(2)),
            'tags': m.group(3).strip(),
            'note': m.group(4).strip() if m.group(4) else None,
        })
    return entries

def format_tags(tags_str):
    """Format tags as backtick-wrapped space-separated."""
    tags = [t.strip() for t in tags_str.split(',') if t.strip()]
    return ' '.join(f'`{t}`' for t in tags)

def build_entry_block(score, tags_str, note):
    emoji = get_emoji(score)
    tag_formatted = format_tags(tags_str)
    block = f"### {emoji} 评分: {score}/10\n\n**标签**: {tag_formatted}\n"
    if note:
        block += f"\n**备注**: {note}\n"
    return block

def build_file_content(date_str, entries, timestamp_str):
    header = f"# {date_str} 心情日记\n\n## 今日心情\n\n"
    body = "\n".join(entries)
    footer = f"\n---\n*记录时间: {timestamp_str}*\n"
    return header + body + footer

def main():
    parser = argparse.ArgumentParser(description='Log daily mood to Obsidian vault.')
    parser.add_argument('--date', type=str, default=datetime.now().strftime('%Y-%m-%d'),
                        help='Date in YYYY-MM-DD format')
    parser.add_argument('--score', type=int, required=True, help='Mood score (1-10)')
    parser.add_argument('--tags', type=str, required=True, help='Comma-separated mood tags')
    parser.add_argument('--note', type=str, default=None, help='Optional note/reason')
    args = parser.parse_args()

    if not (1 <= args.score <= 10):
        print("Error: score must be between 1 and 10")
        return 1

    save_dir = SAVE_DIR
    os.makedirs(save_dir, exist_ok=True)

    filename = f"心情日记-{args.date}.md"
    filepath = os.path.join(save_dir, filename)

    new_entry_block = build_entry_block(args.score, args.tags, args.note)
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')

    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            existing_content = f.read()
        # Find the insertion point: before the footer (---)
        footer_idx = existing_content.rfind('\n---\n')
        if footer_idx != -1:
            pre_footer = existing_content[:footer_idx]
            # Add new entry
            updated_body = pre_footer + "\n" + new_entry_block
            updated_content = updated_body + f"\n---\n*记录时间: {now_str}*\n"
        else:
            # Fallback: append
            updated_content = existing_content + "\n" + new_entry_block + f"\n---\n*记录时间: {now_str}*\n"
    else:
        updated_content = build_file_content(args.date, [new_entry_block], now_str)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(updated_content)

    print(f"✅ 心情已记录: {filepath}")
    print(f"   日期: {args.date} | 评分: {args.score}/10 | 标签: {args.tags}")
    if args.note:
        print(f"   备注: {args.note}")
    return 0

if __name__ == '__main__':
    exit(main())
'''

with open(os.path.join(scripts_dir, "log_mood.py"), "w", encoding="utf-8") as f:
    f.write(log_mood_script)

# --- Write weekly_mood_report.py ---
weekly_report_script = r'''#!/usr/bin/env python3
"""Generate weekly mood report from Obsidian vault mood logs."""
import argparse
import os
import re
import sys
from datetime import datetime, timedelta
from collections import Counter

SAVE_DIR = "/mnt/c/Users/loong/iCloudDrive/iCloud~md~obsidian/HomeMo.Art/05-Daily"

def get_week_range(date_str=None):
    if date_str:
        ref = datetime.strptime(date_str, '%Y-%m-%d')
    else:
        ref = datetime.now()
    # Week: Monday to Sunday
    monday = ref - timedelta(days=ref.weekday())
    sunday = monday + timedelta(days=6)
    return monday.date(), sunday.date()

def parse_mood_file(filepath):
    """Parse a mood log file and return list of (score, tags_list, note) tuples."""
    entries = []
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    # Match each entry block
    pattern = re.compile(
        r'### .+? 评分: (\d+)/10\n\n\*\*标签\*\*: (.+?)\n(?:\n\*\*备注\*\*: (.+?)\n)?',
        re.DOTALL
    )
    for m in pattern.finditer(content):
        score = int(m.group(1))
        raw_tags = m.group(2).strip()
        note = m.group(3).strip() if m.group(3) else None
        # Parse backtick tags
        tags = re.findall(r'`([^`]+)`', raw_tags)
        entries.append((score, tags, note))
    return entries

def generate_report(monday, sunday, save_dir):
    daily_data = {}
    all_tags = Counter()
    all_scores = []
    all_notes = []

    current = monday
    while current <= sunday:
        date_str = current.strftime('%Y-%m-%d')
        filepath = os.path.join(save_dir, f"心情日记-{date_str}.md")
        if os.path.exists(filepath):
            entries = parse_mood_file(filepath)
            if entries:
                day_scores = [e[0] for e in entries]
                daily_data[date_str] = day_scores
                all_scores.extend(day_scores)
                for _, tags, note in entries:
                    all_tags.update(tags)
                    if note:
                        all_notes.append(f"  - {date_str}: {note}")
        current += timedelta(days=1)

    lines = []
    lines.append(f"# 心情周报 ({monday} ~ {sunday})\n")

    if not all_scores:
        lines.append("本周暂无心情记录。\n")
        return '\n'.join(lines)

    avg_score = sum(all_scores) / len(all_scores)
    max_score = max(all_scores)
    min_score = min(all_scores)

    lines.append(f"## 📊 本周统计\n")
    lines.append(f"- **平均心情分**: {avg_score:.1f}/10")
    lines.append(f"- **最高心情**: {max_score}/10")
    lines.append(f"- **最低心情**: {min_score}/10")
    lines.append(f"- **记录天数**: {len(daily_data)}天\n")

    lines.append(f"## 🏷️ 心情标签 TOP5\n")
    for tag, count in all_tags.most_common(5):
        lines.append(f"- `{tag}`: {count}次")
    lines.append("")

    lines.append(f"## 📈 每日心情走势\n")
    current = monday
    while current <= sunday:
        date_str = current.strftime('%Y-%m-%d')
        weekday = current.strftime('%A')
        if date_str in daily_data:
            scores_str = ', '.join(str(s) for s in daily_data[date_str])
            lines.append(f"- {date_str} ({weekday}): {scores_str}/10")
        else:
            lines.append(f"- {date_str} ({weekday}): 无记录")
        current += timedelta(days=1)
    lines.append("")

    if all_notes:
        lines.append(f"## 📝 备注摘录\n")
        lines.extend(all_notes)
        lines.append("")

    lines.append(f"---\n*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")
    return '\n'.join(lines)

def main():
    parser = argparse.ArgumentParser(description='Generate weekly mood report.')
    parser.add_argument('--date', type=str, default=None,
                        help='Any date within the target week (YYYY-MM-DD), defaults to current week')
    parser.add_argument('--output', type=str, default=None,
                        help='Output file path. If not specified, prints to console.')
    args = parser.parse_args()

    monday, sunday = get_week_range(args.date)
    save_dir = SAVE_DIR

    report = generate_report(monday, sunday, save_dir)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✅ 周报已保存: {args.output}")
    else:
        print(report)

if __name__ == '__main__':
    main()
'''

with open(os.path.join(scripts_dir, "weekly_mood_report.py"), "w", encoding="utf-8") as f:
    f.write(weekly_report_script)

# --- Write send_weekly_report.py stub ---
send_report_stub = '''#!/usr/bin/env python3
"""Stub: Send weekly report via WeChat."""
print("Send stub - not used in this task.")
'''
with open(os.path.join(scripts_dir, "send_weekly_report.py"), "w", encoding="utf-8") as f:
    f.write(send_report_stub)

# --- Write SKILL.md ---
skill_md = """---
name: mood-logger
version: 1.0.0
description: 记录每日心情并保存到 Obsidian 库。
---

# 心情日记

使用 Python 脚本记录心情：

```bash
python3 ~/.openclaw/workspace/skills/mood-logger/scripts/log_mood.py \\
  --date 2026-03-27 \\
  --score 8 \\
  --tags "开心,充实" \\
  --note "今天完成了重要任务"
```
"""
with open(os.path.join(skill_base, "SKILL.md"), "w", encoding="utf-8") as f:
    f.write(skill_md)

# --- Print summary ---
print("Workspace initialized.")
print(f"  Scripts:  {scripts_dir}")
print(f"  Obsidian: {obsidian_dir}")
print(f"  Distractors: {len(distractor_files)} files created")