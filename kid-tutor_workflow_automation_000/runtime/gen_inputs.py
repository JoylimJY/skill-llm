import os
import json
import random
import shutil
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# ─── Create the scripts directory ───────────────────────────────────────────
scripts_dir = workspace / "scripts"
scripts_dir.mkdir(exist_ok=True)

# manage_profile.py — handles init and log-session
manage_profile_code = r'''#!/usr/bin/env python3
"""
manage_profile.py  <data_dir> <command> [options]

Commands:
  init          Create a new child profile.
                Required flags: --name, --age, --grade, --interests
  log-session   Read a session JSON from stdin and append to sessions/.
"""
import argparse
import json
import sys
import os
from pathlib import Path
from datetime import datetime


def cmd_init(data_dir: Path, args):
    data_dir.mkdir(parents=True, exist_ok=True)
    profile_path = data_dir / "profile.json"
    if profile_path.exists():
        print(f"[WARN] Profile already exists at {profile_path}. Overwriting.")
    profile = {
        "name": args.name,
        "age": int(args.age),
        "grade": int(args.grade),
        "interests": [i.strip() for i in args.interests.split(",")],
        "difficulty": 1,
        "weak_topics": [],
        "created_at": datetime.now().isoformat()
    }
    profile_path.write_text(json.dumps(profile, ensure_ascii=False, indent=2))
    print(f"[OK] Profile created: {profile_path}")


def cmd_log_session(data_dir: Path, args):
    profile_path = data_dir / "profile.json"
    if not profile_path.exists():
        print(f"[ERROR] No profile found at {profile_path}. Run 'init' first.", file=sys.stderr)
        sys.exit(1)

    sessions_dir = data_dir / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)

    raw = sys.stdin.read().strip()
    try:
        session_data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON from stdin: {e}", file=sys.stderr)
        sys.exit(1)

    # Validate required fields
    required_keys = {"duration_minutes", "questions"}
    missing = required_keys - set(session_data.keys())
    if missing:
        print(f"[ERROR] Session JSON missing keys: {missing}", file=sys.stderr)
        sys.exit(1)

    valid_results = {"correct", "helped", "incorrect"}
    for i, q in enumerate(session_data.get("questions", [])):
        result = q.get("result", "")
        if result not in valid_results:
            print(f"[ERROR] Question {i}: invalid result '{result}'. Must be one of {valid_results}", file=sys.stderr)
            sys.exit(1)
        if not isinstance(q.get("difficulty"), int):
            print(f"[ERROR] Question {i}: 'difficulty' must be an integer.", file=sys.stderr)
            sys.exit(1)

    # Filename: YYYY-MM-DD_HHMM.json
    now = datetime.now()
    filename = now.strftime("%Y-%m-%d_%H%M") + ".json"
    session_path = sessions_dir / filename
    # Avoid overwriting if file exists (add suffix)
    counter = 1
    while session_path.exists():
        filename = now.strftime("%Y-%m-%d_%H%M") + f"_{counter}.json"
        session_path = sessions_dir / filename
        counter += 1

    session_data["saved_at"] = now.isoformat()
    session_path.write_text(json.dumps(session_data, ensure_ascii=False, indent=2))
    print(f"[OK] Session saved: {session_path}")

    # Update weak_topics in profile based on incorrect/helped
    profile = json.loads(profile_path.read_text())
    weak = set(profile.get("weak_topics", []))
    correct_topics = set()
    for q in session_data["questions"]:
        topic = q.get("topic", "")
        if q.get("result") in ("incorrect", "helped"):
            weak.add(topic)
        elif q.get("result") == "correct":
            correct_topics.add(topic)
    # Remove from weak if consistently correct
    weak -= correct_topics
    profile["weak_topics"] = sorted(weak)
    profile_path.write_text(json.dumps(profile, ensure_ascii=False, indent=2))
    print(f"[OK] Profile updated with weak_topics: {profile['weak_topics']}")


def main():
    parser = argparse.ArgumentParser(description="Manage kid-tutor profiles and sessions.")
    parser.add_argument("data_dir", help="Path to the child's data directory, e.g. data/kid-tutor/xiaoming")
    parser.add_argument("command", choices=["init", "log-session"])
    parser.add_argument("--name", default="")
    parser.add_argument("--age", default="")
    parser.add_argument("--grade", default="")
    parser.add_argument("--interests", default="")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)

    if args.command == "init":
        for field, val in [("--name", args.name), ("--age", args.age),
                           ("--grade", args.grade), ("--interests", args.interests)]:
            if not val:
                print(f"[ERROR] {field} is required for init.", file=sys.stderr)
                sys.exit(1)
        cmd_init(data_dir, args)
    elif args.command == "log-session":
        cmd_log_session(data_dir, args)


if __name__ == "__main__":
    main()
'''

(scripts_dir / "manage_profile.py").write_text(manage_profile_code)

# generate_report.py
generate_report_code = r'''#!/usr/bin/env python3
"""
generate_report.py  <data_dir> --days <N>

Generates a parent-facing learning report for the past N days.
Reads from data_dir/sessions/*.json and data_dir/profile.json.
Outputs a JSON report to data_dir/report_last_<N>days.json and prints a summary.
"""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("data_dir", help="Child data directory")
    parser.add_argument("--days", type=int, required=True, help="Number of past days to cover")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    profile_path = data_dir / "profile.json"
    sessions_dir = data_dir / "sessions"

    if not profile_path.exists():
        print(f"[ERROR] No profile at {profile_path}", file=sys.stderr)
        sys.exit(1)

    profile = json.loads(profile_path.read_text())
    cutoff = datetime.now() - timedelta(days=args.days)

    session_files = list(sessions_dir.glob("*.json")) if sessions_dir.exists() else []
    sessions = []
    for sf in sorted(session_files):
        try:
            data = json.loads(sf.read_text())
            saved_at_str = data.get("saved_at", "")
            if saved_at_str:
                saved_at = datetime.fromisoformat(saved_at_str)
                if saved_at >= cutoff:
                    sessions.append(data)
            else:
                sessions.append(data)
        except Exception:
            pass

    total_questions = 0
    correct_count = 0
    helped_count = 0
    incorrect_count = 0
    topic_stats = defaultdict(lambda: {"correct": 0, "helped": 0, "incorrect": 0})
    total_minutes = 0

    for s in sessions:
        total_minutes += s.get("duration_minutes", 0)
        for q in s.get("questions", []):
            total_questions += 1
            r = q.get("result", "")
            topic = q.get("topic", "unknown")
            topic_stats[topic][r] = topic_stats[topic].get(r, 0) + 1
            if r == "correct":
                correct_count += 1
            elif r == "helped":
                helped_count += 1
            elif r == "incorrect":
                incorrect_count += 1

    accuracy = round(correct_count / total_questions * 100, 1) if total_questions > 0 else 0.0

    weak_topics = [
        t for t, s in topic_stats.items()
        if s.get("incorrect", 0) + s.get("helped", 0) > s.get("correct", 0)
    ]

    report = {
        "child_name": profile.get("name"),
        "grade": profile.get("grade"),
        "report_days": args.days,
        "generated_at": datetime.now().isoformat(),
        "total_sessions": len(sessions),
        "total_minutes": total_minutes,
        "total_questions": total_questions,
        "correct": correct_count,
        "helped": helped_count,
        "incorrect": incorrect_count,
        "accuracy_percent": accuracy,
        "weak_topics": weak_topics,
        "topic_breakdown": dict(topic_stats),
        "suggestions": [
            f"重点复习: {t}" for t in weak_topics
        ] if weak_topics else ["继续保持！各知识点掌握良好。"]
    }

    report_path = data_dir / f"report_last_{args.days}days.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\n[OK] Report saved to {report_path}")


if __name__ == "__main__":
    main()
'''

(scripts_dir / "generate_report.py").write_text(generate_report_code)

# ─── References directory ───────────────────────────────────────────────────
refs_dir = workspace / "references"
refs_dir.mkdir(exist_ok=True)

curriculum_content = """# 小学课程知识点对照表

## 一年级 (Grade 1)
- 数学: 20以内加减法, 认识图形
- 科学: 身边的动植物, 天气观察

## 二年级 (Grade 2)
- 数学: 100以内加减法, 乘法口诀
- 科学: 植物生长, 简单机械

## 三年级 (Grade 3)
- 数学: 两位数乘除法, 分数入门
- 科学: 动物分类, 水的循环

## 四年级 (Grade 4)
- 数学: 三位数运算, 小数, 面积
- 科学: 物质变化, 生态系统

## 五年级 (Grade 5)
- 数学: 方程, 比例, 图形变换
- 科学: 力与运动, 地球与宇宙

## 六年级 (Grade 6)
- 数学: 统计与概率, 圆的计算
- 科学: 物理变化与化学变化, 能量转换
"""
(refs_dir / "curriculum.md").write_text(curriculum_content)

pedagogy_content = """# 苏格拉底式教学法指引

## 核心原则
1. 永远不直接给答案
2. 用追问拆解问题
3. 错误时不否定，引导验证
4. 2-3轮引导后切换讲解模式

## 常用引导语
- "题目告诉了我们什么信息？"
- "如果按你说的算，会得到什么呢？"
- "我们先算哪一步？"
- "能不能用别的方法验证一下？"
"""
(refs_dir / "pedagogy.md").write_text(pedagogy_content)

question_templates_content = """# 出题模板参考

## 数学题模板
- [人物]有[N1]个[物品]，又得到[N2]个，一共有多少个？
- [场景]中有[N1]行[N2]列，共有多少个？

## 科学题模板
- [动物]属于哪一类？
- 水从液态变成气态叫做什么？
"""
(refs_dir / "question-templates.md").write_text(question_templates_content)

# ─── Distractor files ────────────────────────────────────────────────────────
distractor_dir = workspace / "data" / "kid-tutor"
distractor_dir.mkdir(parents=True, exist_ok=True)

# Another child's existing data (distractor)
other_child_dir = distractor_dir / "xiaomei"
other_child_dir.mkdir(exist_ok=True)
other_profile = {
    "name": "小美",
    "age": 9,
    "grade": 3,
    "interests": ["画画", "公主"],
    "difficulty": 2,
    "weak_topics": ["分数入门"],
    "created_at": "2026-01-10T09:00:00"
}
(other_child_dir / "profile.json").write_text(json.dumps(other_profile, ensure_ascii=False, indent=2))
other_sessions_dir = other_child_dir / "sessions"
other_sessions_dir.mkdir(exist_ok=True)
old_session = {
    "duration_minutes": 12,
    "questions": [
        {"subject": "数学", "topic": "分数入门", "difficulty": 2,
         "question": "1/2 + 1/4 = ?", "result": "helped", "attempts": 2, "notes": ""}
    ],
    "saved_at": "2026-01-15T10:30:00"
}
(other_sessions_dir / "2026-01-15_1030.json").write_text(json.dumps(old_session, ensure_ascii=False, indent=2))

# Logs and misc distractor files
logs_dir = workspace / "logs"
logs_dir.mkdir(exist_ok=True)
for i in range(3):
    (logs_dir / f"system_{i}.log").write_text(f"[INFO] system startup log {i}\n[DEBUG] nothing here\n")

(workspace / "config.yaml").write_text("app: kid-tutor\nversion: 1.2.0\nenv: production\n")
(workspace / "requirements.txt").write_text("flask\nrequests\n")

tmp_dir = workspace / "tmp"
tmp_dir.mkdir(exist_ok=True)
(tmp_dir / "draft_session.txt").write_text("this is not a valid session\n")
(tmp_dir / "notes.txt").write_text("remember to add more topics\n")

archive_dir = workspace / "archive" / "2025"
archive_dir.mkdir(parents=True, exist_ok=True)
(archive_dir / "old_profile_template.json").write_text('{"name":"","age":0,"grade":0}\n')
(archive_dir / "deprecated_script.py").write_text("# deprecated\nprint('old code')\n")

print("Workspace generated successfully.")
print(f"Structure:\n")
for p in sorted(workspace.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(workspace)}")