import os
import json
import random
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

workspace = Path("/workspace")

# --- Create the mood-diary skill directory structure ---
skill_root = workspace / "mood-diary"
skill_root.mkdir(parents=True, exist_ok=True)

scripts_dir = skill_root / "scripts"
scripts_dir.mkdir(exist_ok=True)

assets_dir = skill_root / "assets"
assets_dir.mkdir(exist_ok=True)

# --- Create assets/moods.json ---
moods_json = {
    "moods": {
        "开心": {
            "score_range": [7, 9],
            "keywords": ["开心", "高兴", "快乐", "愉快", "欢喜", "喜悦", "美滋滋", "哈哈", "嘿嘿"],
            "emoji": "😊",
            "color": "#FFD93D"
        },
        "平静": {
            "score_range": [5, 7],
            "keywords": ["平静", "平和", "安宁", "淡定", "从容", "安稳", "宁静", "祥和"],
            "emoji": "😌",
            "color": "#95E1D3"
        },
        "兴奋": {
            "score_range": [8, 10],
            "keywords": ["兴奋", "激动", "亢奋", "狂喜", "太棒了", "绝了", "燃", "起飞"],
            "emoji": "🤩",
            "color": "#F38181"
        },
        "焦虑": {
            "score_range": [3, 5],
            "keywords": ["焦虑", "担心", "紧张", "不安", "忐忑", "发愁", "压力大", "迷茫"],
            "emoji": "😰",
            "color": "#FCE38A"
        },
        "难过": {
            "score_range": [1, 4],
            "keywords": ["难过", "伤心", "悲伤", "失落", "沮丧", "郁闷", "委屈", "想哭", "emo"],
            "emoji": "😢",
            "color": "#6C5CE7"
        },
        "愤怒": {
            "score_range": [2, 5],
            "keywords": ["愤怒", "生气", "恼火", "气愤", "不爽", "烦躁", "火大", "爆炸"],
            "emoji": "😡",
            "color": "#FF4757"
        },
        "疲惫": {
            "score_range": [2, 5],
            "keywords": ["疲惫", "累", "疲倦", "困", "乏力", "没精神"],
            "emoji": "😴",
            "color": "#A29BFE"
        }
    },
    "tag_patterns": {
        "人": ["朋友", "家人", "同事", "老板", "同学", "对象"],
        "事": ["工作", "学习", "考试", "项目", "会议", "面试"],
        "物": ["咖啡", "茶", "书", "电影", "音乐", "游戏"],
        "地点": ["公司", "家", "学校", "咖啡店", "公园"],
        "天气": ["晴天", "阴天", "下雨", "下雪", "热", "冷"]
    }
}

with open(assets_dir / "moods.json", "w", encoding="utf-8") as f:
    json.dump(moods_json, f, ensure_ascii=False, indent=2)

# --- Create scripts/journal.py ---
journal_py = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
心情日记 - 核心日记模块
"""

import json
import os
import sys
import re
import uuid
from datetime import datetime, timedelta
from pathlib import Path


DATA_DIR = Path.home() / ".openclaw" / "workspace" / "data" / "journal"
DATA_FILE = DATA_DIR / "entries.json"


def ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_data():
    ensure_data_dir()
    if not DATA_FILE.exists():
        return {"entries": [], "version": "1.0"}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    ensure_data_dir()
    tmp_file = DATA_FILE.with_suffix(".tmp")
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp_file.replace(DATA_FILE)


def load_moods_config():
    script_dir = Path(__file__).parent.parent
    moods_file = script_dir / "assets" / "moods.json"
    if moods_file.exists():
        with open(moods_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"moods": {}, "tag_patterns": {}}


def generate_id():
    return str(uuid.uuid4())[:8]


def parse_date(text):
    today = datetime.now().date()
    if "前天" in text:
        return str(today - timedelta(days=2))
    elif "昨天" in text:
        return str(today - timedelta(days=1))
    elif "今天" in text:
        return str(today)
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
    if date_match:
        return date_match.group(1)
    return str(today)


def parse_score(text):
    patterns = [
        r'心情(\d+)分',
        r'评分(\d+)',
        r'mood\s*(\d+)',
        r'(\d+)/10',
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            score = int(m.group(1))
            return max(1, min(10, score))
    return None


def detect_mood(text, moods_config):
    moods = moods_config.get("moods", {})
    for mood_name, mood_data in moods.items():
        for kw in mood_data.get("keywords", []):
            if kw in text:
                return mood_name
    return "平静"


def infer_score_from_mood(mood, moods_config):
    moods = moods_config.get("moods", {})
    if mood in moods:
        r = moods[mood]["score_range"]
        return (r[0] + r[1]) // 2
    return 5


def extract_tags(text, moods_config):
    tags = []
    tag_patterns = moods_config.get("tag_patterns", {})
    for category, keywords in tag_patterns.items():
        for kw in keywords:
            if kw in text:
                tags.append(kw)
    return list(set(tags))


def clean_content(text):
    # Remove score patterns and date expressions from content
    text = re.sub(r'心情\d+分', '', text)
    text = re.sub(r'评分\d+', '', text)
    text = re.sub(r'mood\s*\d+', '', text)
    text = re.sub(r'\d+/10', '', text)
    text = text.replace("今天", "").replace("昨天", "").replace("前天", "")
    text = text.strip("，。 ,.")
    return text.strip()


class JournalTracker:
    def __init__(self):
        self.moods_config = load_moods_config()

    def add(self, raw_text):
        data = load_data()
        date = parse_date(raw_text)
        score = parse_score(raw_text)
        mood = detect_mood(raw_text, self.moods_config)
        if score is None:
            score = infer_score_from_mood(mood, self.moods_config)
        tags = extract_tags(raw_text, self.moods_config)
        content = clean_content(raw_text)
        now = datetime.now().isoformat(timespec='seconds')
        entry = {
            "id": generate_id(),
            "date": date,
            "content": content,
            "mood": mood,
            "score": score,
            "tags": tags,
            "raw_text": raw_text,
            "created_at": now,
            "updated_at": now
        }
        data["entries"].append(entry)
        save_data(data)
        return entry

    def list_entries(self, days=7, mood_filter=None):
        data = load_data()
        cutoff = str((datetime.now().date() - timedelta(days=days)))
        entries = [e for e in data["entries"] if e["date"] >= cutoff]
        if mood_filter:
            entries = [e for e in entries if e["mood"] == mood_filter]
        return sorted(entries, key=lambda x: x["date"], reverse=True)

    def get_summary(self, days=30):
        entries = self.list_entries(days=days)
        if not entries:
            return {"count": 0, "avg_score": 0, "mood_distribution": {}, "days": days}
        scores = [e["score"] for e in entries]
        mood_dist = {}
        for e in entries:
            mood_dist[e["mood"]] = mood_dist.get(e["mood"], 0) + 1
        return {
            "count": len(entries),
            "avg_score": round(sum(scores) / len(scores), 2),
            "mood_distribution": mood_dist,
            "days": days
        }

    def update(self, entry_id, new_text):
        data = load_data()
        for entry in data["entries"]:
            if entry["id"] == entry_id:
                score = parse_score(new_text)
                mood = detect_mood(new_text, self.moods_config)
                if score is None:
                    score = infer_score_from_mood(mood, self.moods_config)
                tags = extract_tags(new_text, self.moods_config)
                content = clean_content(new_text)
                entry["content"] = content
                entry["mood"] = mood
                entry["score"] = score
                entry["tags"] = tags
                entry["raw_text"] = new_text
                entry["updated_at"] = datetime.now().isoformat(timespec='seconds')
                save_data(data)
                return entry
        return None

    def delete(self, entry_id):
        data = load_data()
        before = len(data["entries"])
        data["entries"] = [e for e in data["entries"] if e["id"] != entry_id]
        save_data(data)
        return len(data["entries"]) < before

    def calendar(self, year=None, month=None):
        today = datetime.now().date()
        if year is None:
            year = today.year
        if month is None:
            month = today.month
        data = load_data()
        prefix = f"{year:04d}-{month:02d}"
        entries = [e for e in data["entries"] if e["date"].startswith(prefix)]
        day_map = {}
        for e in entries:
            day = e["date"]
            if day not in day_map:
                day_map[day] = []
            day_map[day].append(e)
        return day_map

    def get_moods(self):
        return list(self.moods_config.get("moods", {}).keys())


def cmd_add(args):
    if not args:
        print("用法: add <内容>")
        sys.exit(1)
    text = " ".join(args)
    tracker = JournalTracker()
    entry = tracker.add(text)
    print(f"✅ 日记已添加")
    print(f"   ID: {entry['id']}")
    print(f"   日期: {entry['date']}")
    print(f"   情绪: {entry['mood']}")
    print(f"   评分: {entry['score']}")
    print(f"   标签: {', '.join(entry['tags']) if entry['tags'] else '无'}")


def cmd_list(args):
    days = int(args[0]) if args else 7
    mood_filter = args[1] if len(args) > 1 else None
    tracker = JournalTracker()
    entries = tracker.list_entries(days=days, mood_filter=mood_filter)
    if not entries:
        print("📭 没有找到日记记录")
        return
    print(f"📚 最近{days}天的日记 ({len(entries)}条):")
    for e in entries:
        tags_str = f" [{', '.join(e['tags'])}]" if e['tags'] else ""
        print(f"  {e['date']} | {e['mood']} | {e['score']}分 | {e['content'][:30]}{tags_str}")


def cmd_summary(args):
    days = int(args[0]) if args else 30
    tracker = JournalTracker()
    s = tracker.get_summary(days=days)
    print(f"📊 情绪摘要 (最近{days}天):")
    print(f"   记录数: {s['count']}")
    print(f"   平均分: {s['avg_score']}")
    print(f"   情绪分布: {s['mood_distribution']}")


def cmd_delete(args):
    if not args:
        print("用法: delete <ID>")
        sys.exit(1)
    tracker = JournalTracker()
    ok = tracker.delete(args[0])
    if ok:
        print(f"🗑️  已删除 {args[0]}")
    else:
        print(f"❌ 未找到 {args[0]}")


def cmd_update(args):
    if len(args) < 2:
        print("用法: update <ID> <内容>")
        sys.exit(1)
    entry_id = args[0]
    new_text = " ".join(args[1:])
    tracker = JournalTracker()
    entry = tracker.update(entry_id, new_text)
    if entry:
        print(f"✅ 已更新 {entry_id}")
        print(f"   情绪: {entry['mood']}")
        print(f"   评分: {entry['score']}")
    else:
        print(f"❌ 未找到 {entry_id}")


def cmd_moods(args):
    tracker = JournalTracker()
    moods = tracker.get_moods()
    print("🎭 支持的情绪类型:")
    for m in moods:
        print(f"  - {m}")


def cmd_calendar(args):
    year = int(args[0]) if len(args) > 0 else None
    month = int(args[1]) if len(args) > 1 else None
    tracker = JournalTracker()
    day_map = tracker.calendar(year, month)
    if not day_map:
        print("📅 本月没有日记")
        return
    print("📅 心情日历:")
    for day in sorted(day_map.keys()):
        entries = day_map[day]
        moods_str = ", ".join([e["mood"] for e in entries])
        avg_score = sum(e["score"] for e in entries) / len(entries)
        print(f"  {day}: {moods_str} (avg: {avg_score:.1f})")


def main():
    if len(sys.argv) < 2:
        print("用法: journal.py <命令> [参数]")
        print("命令: add, list, calendar, summary, delete, moods, update")
        sys.exit(1)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        "add": cmd_add,
        "list": cmd_list,
        "summary": cmd_summary,
        "delete": cmd_delete,
        "update": cmd_update,
        "moods": cmd_moods,
        "calendar": cmd_calendar,
    }

    if cmd not in commands:
        print(f"❌ 未知命令: {cmd}")
        sys.exit(1)

    commands[cmd](args)


if __name__ == "__main__":
    main()
'''

with open(scripts_dir / "journal.py", "w", encoding="utf-8") as f:
    f.write(journal_py)

# --- Create scripts/mood-report.py ---
mood_report_py = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
心情日记 - 情绪报告生成器
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path.home() / ".openclaw" / "workspace" / "data" / "journal"
DATA_FILE = DATA_DIR / "entries.json"


def load_data():
    if not DATA_FILE.exists():
        return {"entries": [], "version": "1.0"}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_entries_for_period(start_date, end_date):
    data = load_data()
    start_str = str(start_date)
    end_str = str(end_date)
    return [e for e in data["entries"] if start_str <= e["date"] <= end_str]


def daily_report(date_str=None):
    if date_str is None:
        date_str = str(datetime.now().date())
    entries = get_entries_for_period(date_str, date_str)
    print(f"\n📅 日报: {date_str}")
    print("=" * 40)
    if not entries:
        print("  当日无记录")
        return
    scores = [e["score"] for e in entries]
    avg = sum(scores) / len(scores)
    print(f"  记录数: {len(entries)}")
    print(f"  平均分: {avg:.1f}")
    mood_dist = {}
    for e in entries:
        mood_dist[e["mood"]] = mood_dist.get(e["mood"], 0) + 1
    print(f"  情绪分布: {mood_dist}")
    print("\n  📝 日记列表:")
    for e in entries:
        print(f"    [{e['mood']} {e['score']}分] {e['content'][:40]}")


def weekly_report(offset=0):
    today = datetime.now().date()
    days_since_monday = today.weekday()
    monday = today - timedelta(days=days_since_monday + 7 * offset)
    sunday = monday + timedelta(days=6)
    entries = get_entries_for_period(monday, sunday)

    print(f"\n📊 周报: {monday} ~ {sunday}")
    print("=" * 40)
    if not entries:
        print("  本周无记录")
        return

    scores = [e["score"] for e in entries]
    avg = sum(scores) / len(scores)
    print(f"  总记录数: {len(entries)}")
    print(f"  周均分: {avg:.1f}")

    # Daily breakdown
    day_scores = {}
    for e in entries:
        d = e["date"]
        if d not in day_scores:
            day_scores[d] = []
        day_scores[d].append(e["score"])

    print("\n  📈 每日情绪:")
    for d in sorted(day_scores.keys()):
        day_avg = sum(day_scores[d]) / len(day_scores[d])
        print(f"    {d}: {day_avg:.1f}分")

    mood_dist = {}
    for e in entries:
        mood_dist[e["mood"]] = mood_dist.get(e["mood"], 0) + 1
    dominant = max(mood_dist, key=mood_dist.get)
    print(f"\n  🎭 主导情绪: {dominant}")
    print(f"  情绪分布: {mood_dist}")

    # Health advice
    print("\n  💡 健康建议:")
    if avg >= 7:
        print("    情绪状态良好，继续保持！")
    elif avg >= 5:
        print("    情绪基本稳定，注意劳逸结合。")
    else:
        print("    情绪较低，建议多休息、与朋友沟通。")


def monthly_report(offset=0):
    today = datetime.now().date()
    year = today.year
    month = today.month - offset
    while month <= 0:
        month += 12
        year -= 1
    start = datetime(year, month, 1).date()
    if month == 12:
        end = datetime(year + 1, 1, 1).date() - timedelta(days=1)
    else:
        end = datetime(year, month + 1, 1).date() - timedelta(days=1)

    entries = get_entries_for_period(start, end)
    print(f"\n📆 月报: {year}年{month}月")
    print("=" * 40)
    if not entries:
        print("  本月无记录")
        return

    scores = [e["score"] for e in entries]
    avg = sum(scores) / len(scores)
    print(f"  总记录数: {len(entries)}")
    print(f"  月均分: {avg:.1f}")

    # Weekly breakdown
    week_scores = {}
    for e in entries:
        d = datetime.strptime(e["date"], "%Y-%m-%d").date()
        week_num = (d - start).days // 7 + 1
        if week_num not in week_scores:
            week_scores[week_num] = []
        week_scores[week_num].append(e["score"])

    print("\n  📊 每周概况:")
    for w in sorted(week_scores.keys()):
        wk_avg = sum(week_scores[w]) / len(week_scores[w])
        print(f"    第{w}周: {wk_avg:.1f}分")

    mood_dist = {}
    for e in entries:
        mood_dist[e["mood"]] = mood_dist.get(e["mood"], 0) + 1
    dominant = max(mood_dist, key=mood_dist.get)
    print(f"\n  🎭 主导情绪: {dominant}")
    print(f"  情绪分布: {mood_dist}")

    print("\n  💡 月度建议:")
    if avg >= 7:
        print("    本月情绪总体积极，很棒！")
    elif avg >= 5:
        print("    情绪总体平稳，继续记录观察。")
    else:
        print("    情绪偏低，建议关注心理健康。")


def trend_report(days=30):
    today = datetime.now().date()
    start = today - timedelta(days=days)
    entries = get_entries_for_period(start, today)

    print(f"\n📉 趋势分析: 最近{days}天")
    print("=" * 40)
    if not entries:
        print("  无数据")
        return

    scores = [e["score"] for e in entries]
    avg = sum(scores) / len(scores)
    print(f"  总记录数: {len(entries)}")
    print(f"  平均分: {avg:.1f}")

    # Week-by-week
    weeks = {}
    for e in entries:
        d = datetime.strptime(e["date"], "%Y-%m-%d").date()
        week = (today - d).days // 7
        if week not in weeks:
            weeks[week] = []
        weeks[week].append(e["score"])

    print("\n  📈 每周情绪评分:")
    week_avgs = []
    for w in sorted(weeks.keys(), reverse=True):
        wk_avg = sum(weeks[w]) / len(weeks[w])
        week_avgs.append(wk_avg)
        label = "本周" if w == 0 else f"{w}周前"
        print(f"    {label}: {wk_avg:.1f}分")

    # Trend direction
    if len(week_avgs) >= 2:
        if week_avgs[0] > week_avgs[-1] + 0.5:
            trend = "上升 📈"
        elif week_avgs[0] < week_avgs[-1] - 0.5:
            trend = "下降 📉"
        else:
            trend = "稳定 ➡️"
        print(f"\n  🔮 情绪趋势: {trend}")

    # Anomaly detection
    if scores:
        mean = sum(scores) / len(scores)
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        std = variance ** 0.5
        anomalies = [e for e in entries if abs(e["score"] - mean) > 2 * std]
        if anomalies:
            print(f"\n  ⚠️  情绪波动异常 ({len(anomalies)}次):")
            for a in anomalies:
                print(f"    {a['date']}: {a['score']}分 ({a['mood']})")

    print("\n  💡 长期健康建议:")
    if avg >= 7:
        print("    长期情绪积极，请继续保持良好生活习惯。")
    elif avg >= 5:
        print("    情绪总体平稳，注意保持作息规律。")
    else:
        print("    情绪持续偏低，建议寻求专业心理健康支持。")


def main():
    if len(sys.argv) < 2:
        print("用法: mood-report.py <命令> [参数]")
        print("命令: daily, weekly, monthly, trend")
        sys.exit(1)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd == "daily":
        daily_report(args[0] if args else None)
    elif cmd == "weekly":
        weekly_report(int(args[0]) if args else 0)
    elif cmd == "monthly":
        monthly_report(int(args[0]) if args else 0)
    elif cmd == "trend":
        trend_report(int(args[0]) if args else 30)
    else:
        print(f"❌ 未知命令: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
'''

with open(scripts_dir / "mood-report.py", "w", encoding="utf-8") as f:
    f.write(mood_report_py)

# Make scripts executable
os.chmod(scripts_dir / "journal.py", 0o755)
os.chmod(scripts_dir / "mood-report.py", 0o755)

# --- Create SKILL.md in root ---
skill_md_content = """---
name: mood-diary
version: 1.0.0
description: >
  心情日记 — 智能情绪追踪器
---

# See full documentation in mood-diary/SKILL.md
"""
with open(workspace / "SKILL.md", "w", encoding="utf-8") as f:
    f.write(skill_md_content)

# --- Create distractor files ---
distractors = [
    ("README_old.txt", "This is an outdated readme. Ignore."),
    ("config/app.yaml", "debug: false\nport: 8080\nlog_level: info\n"),
    ("config/secrets.yaml", "# DO NOT COMMIT\napi_key: PLACEHOLDER\n"),
    ("data/sample_data.csv", "date,value\n2024-01-01,5\n2024-01-02,6\n"),
    ("data/archive/old_entries.json", json.dumps({"entries": [], "version": "0.9"})),
    ("logs/app.log", "2024-01-01 10:00:00 INFO Starting application\n"),
    ("logs/error.log", "2024-01-01 10:05:00 ERROR Connection refused\n"),
    ("tests/test_placeholder.py", "# TODO: write tests\ndef test_nothing(): pass\n"),
    ("notes/meeting_notes.md", "# Meeting Notes\n- Discussed Q1 roadmap\n- Action items pending\n"),
    ("notes/todo.txt", "1. Fix bug in parser\n2. Update documentation\n3. Deploy to staging\n"),
    ("scripts/legacy_export.py", "# Deprecated\nprint('This script is deprecated')\n"),
    ("backup/entries_backup.json", json.dumps({"entries": [{"id": "deadbeef", "date": "2023-12-01", "content": "old backup", "mood": "平静", "score": 5, "tags": [], "raw_text": "old backup", "created_at": "2023-12-01T10:00:00", "updated_at": "2023-12-01T10:00:00"}], "version": "1.0"})),
]

for rel_path, content in distractors:
    fp = workspace / rel_path
    fp.parent.mkdir(parents=True, exist_ok=True)
    with open(fp, "w", encoding="utf-8") as f:
        f.write(content)

# --- Create the task brief (the raw messy input the agent must process) ---
# This is a "week_log.txt" file containing rough notes that need to be entered as diary entries
# The agent must parse this into proper entries using the mood diary system.

from datetime import datetime, timedelta

today = datetime.now().date()
days = {
    "6_days_ago": str(today - timedelta(days=6)),
    "5_days_ago": str(today - timedelta(days=5)),
    "4_days_ago": str(today - timedelta(days=4)),
    "3_days_ago": str(today - timedelta(days=3)),
    "2_days_ago": str(today - timedelta(days=2)),
    "yesterday": str(today - timedelta(days=1)),
    "today": str(today),
}

task_brief = f"""员工情绪追踪周记录 - 待录入系统
============================================
以下是本周的情绪日记草稿，需要录入情绪追踪系统。

【日期: {days['6_days_ago']}】
今天周一项目启动会，虽然任务重但感觉燃起来了，心情9分

【日期: {days['5_days_ago']}】
今天和同事开会讨论方案，下午喝了咖啡，感觉挺平静的

【日期: {days['4_days_ago']}】
今天deadline压力大，一直担心项目能否按时交付，压力大心情5分

【日期: {days['3_days_ago']}】
今天老板批评了我的方案，感觉很委屈，emo了一整天，心情3分

【日期: {days['2_days_ago']}】
前一天的情绪恢复了一些，今天在公园散步，天气不错，心情7分

【日期: {days['yesterday']}】
昨天加班到很晚，真的很累了，没精神

【日期: {days['today']}】
今天朋友来公司找我吃午饭，聊得很开心，心情8分

注意事项：
- {days['3_days_ago']} 的那条记录录入时需要先用"焦虑"相关词汇，但实际应该是"难过"情绪
  （请在录入后用正确的内容更新: "今天老板批评了我的方案，感觉很委屈，想哭，心情3分"）
- 录入完毕后请生成最近7天的趋势分析报告，并将报告内容保存到 trend_report.txt
"""

with open(workspace / "week_log.txt", "w", encoding="utf-8") as f:
    f.write(task_brief)

print("Workspace setup complete.")
print(f"Task brief written to: {workspace}/week_log.txt")
print(f"Mood diary skill installed at: {workspace}/mood-diary/")