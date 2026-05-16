import os
import json
import random
import string
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── Skill directory structure ──────────────────────────────────────────────
skill_dir = workspace / "skills" / "habitchat"
scripts_dir = skill_dir / "scripts"
scripts_dir.mkdir(parents=True, exist_ok=True)

# ── Distractor files ───────────────────────────────────────────────────────
distractor_dirs = [
    workspace / "notes",
    workspace / "projects" / "alpha",
    workspace / "projects" / "beta",
    workspace / "archive" / "2023",
    workspace / "archive" / "2024",
    workspace / "config",
    workspace / "tmp",
    workspace / "logs",
    workspace / "docs",
    workspace / "tools",
]
for d in distractor_dirs:
    d.mkdir(parents=True, exist_ok=True)

distractor_files = {
    workspace / "notes" / "random_notes.txt": "Meeting at 10am. Buy groceries. Call dentist.",
    workspace / "notes" / "ideas.md": "# Ideas\n- Build a habit tracker\n- Learn guitar",
    workspace / "projects" / "alpha" / "config.json": json.dumps({"project": "alpha", "version": "0.1"}),
    workspace / "projects" / "beta" / "settings.yaml": "db_host: localhost\ndb_port: 5432",
    workspace / "archive" / "2023" / "old_habits.csv": "habit,days\nmeditate,30\nexercise,12",
    workspace / "archive" / "2024" / "summary.txt": "Year in review: completed 3 habits consistently.",
    workspace / "config" / "user_prefs.ini": "[user]\nname=Alex\ntimezone=UTC",
    workspace / "tmp" / "scratch.py": "# temp script\nprint('hello')",
    workspace / "logs" / "app.log": "2024-01-01 INFO startup\n2024-01-02 INFO shutdown",
    workspace / "docs" / "README.md": "# Workspace\nThis is a general workspace.",
    workspace / "tools" / "helper.sh": "#!/bin/bash\necho 'helper'",
    workspace / "tools" / "convert.py": "# conversion utility\npass",
}
for path, content in distractor_files.items():
    path.write_text(content)

# ── habit_tracker.py script ────────────────────────────────────────────────
# A fully functional implementation of the habit_tracker CLI described in SKILL.md
habit_tracker_py = r'''#!/usr/bin/env python3
"""
habit_tracker.py - CLI for HabitChat habit tracking system.
Implements: init, add, log, list, stats, overview, edit, pause, resume, delete
"""
import argparse
import json
import os
import sys
import uuid
from datetime import datetime, date, timedelta
from pathlib import Path

DATA_DIR = Path.home() / ".habitchat"
HABITS_FILE = DATA_DIR / "habits.json"
LOGS_FILE = DATA_DIR / "logs.json"
STREAKS_FILE = DATA_DIR / "streaks.json"
CONFIG_FILE = DATA_DIR / "config.json"

VALID_DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
VALID_STATUSES = ["done", "skip", "miss"]

def load_json(path, default):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return default
    return default

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))

def init_cmd(args):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not HABITS_FILE.exists():
        save_json(HABITS_FILE, {"habits": []})
    if not LOGS_FILE.exists():
        save_json(LOGS_FILE, {"logs": []})
    if not STREAKS_FILE.exists():
        save_json(STREAKS_FILE, {"streaks": {}})
    if not CONFIG_FILE.exists():
        save_json(CONFIG_FILE, {"timezone": "UTC", "coaching_style": "encouraging"})
    print("Initialized ~/.habitchat/")

def parse_days(days_str):
    if days_str is None:
        return VALID_DAYS
    days_str = days_str.strip().lower()
    if days_str == "weekdays":
        return ["mon", "tue", "wed", "thu", "fri"]
    if days_str == "weekends":
        return ["sat", "sun"]
    parts = [d.strip() for d in days_str.split(",")]
    validated = []
    for p in parts:
        if p in VALID_DAYS:
            validated.append(p)
        else:
            print(f"Invalid day: {p}. Must be one of {VALID_DAYS}", file=sys.stderr)
            sys.exit(1)
    return validated

def parse_time(time_str):
    if time_str is None:
        return "08:00"
    ts = time_str.strip().lower()
    if ts == "morning":
        return "08:00"
    if ts == "evening":
        return "19:00"
    if ts == "night":
        return "21:00"
    if ts == "after lunch":
        return "13:00"
    if ts == "noon":
        return "12:00"
    # Handle "9am" style
    import re
    m = re.match(r'^(\d{1,2})(am|pm)$', ts)
    if m:
        h = int(m.group(1))
        period = m.group(2)
        if period == "pm" and h != 12:
            h += 12
        if period == "am" and h == 12:
            h = 0
        return f"{h:02d}:00"
    # Already HH:MM
    m2 = re.match(r'^(\d{1,2}):(\d{2})$', ts)
    if m2:
        return f"{int(m2.group(1)):02d}:{m2.group(2)}"
    print(f"Cannot parse time: {time_str}", file=sys.stderr)
    sys.exit(1)

def find_habit(habits_list, identifier):
    identifier = identifier.strip().lower()
    # Try by short UUID
    for h in habits_list:
        if h["id"].lower().startswith(identifier):
            return h
    # Try by exact name (case-insensitive)
    for h in habits_list:
        if h["name"].lower() == identifier:
            return h
    # Try partial name
    matches = [h for h in habits_list if identifier in h["name"].lower()]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        print(f"Ambiguous habit '{identifier}'. Matches: {[h['name'] for h in matches]}", file=sys.stderr)
        sys.exit(1)
    print(f"Habit not found: '{identifier}'", file=sys.stderr)
    sys.exit(1)

def add_cmd(args):
    data = load_json(HABITS_FILE, {"habits": []})
    habit_id = str(uuid.uuid4())[:8]
    habit = {
        "id": habit_id,
        "name": args.name,
        "time": parse_time(args.time),
        "days": parse_days(args.days),
        "created": date.today().isoformat(),
        "paused": False,
    }
    data["habits"].append(habit)
    save_json(HABITS_FILE, data)
    print(f"Added habit: {args.name} (id: {habit_id})")
    print(json.dumps(habit))

def log_cmd(args):
    if args.status not in VALID_STATUSES:
        print(f"Invalid status '{args.status}'. Must be one of {VALID_STATUSES}", file=sys.stderr)
        sys.exit(1)
    data = load_json(HABITS_FILE, {"habits": []})
    habit = find_habit(data["habits"], args.habit)
    logs = load_json(LOGS_FILE, {"logs": []})
    today = date.today().isoformat()
    # Remove any existing log for this habit today
    logs["logs"] = [l for l in logs["logs"] if not (l["habit_id"] == habit["id"] and l["date"] == today)]
    entry = {
        "habit_id": habit["id"],
        "habit_name": habit["name"],
        "date": today,
        "status": args.status,
        "logged_at": datetime.now().isoformat(),
    }
    logs["logs"].append(entry)
    save_json(LOGS_FILE, logs)
    # Compute streak
    streak = compute_streak(habit["id"], logs["logs"])
    streaks = load_json(STREAKS_FILE, {"streaks": {}})
    streaks["streaks"][habit["id"]] = streak
    save_json(STREAKS_FILE, streaks)
    print(f"Logged '{habit['name']}' as {args.status}. Current streak: {streak}")
    print(json.dumps(entry))

def compute_streak(habit_id, logs_list):
    done_dates = sorted(set(
        l["date"] for l in logs_list
        if l["habit_id"] == habit_id and l["status"] == "done"
    ), reverse=True)
    if not done_dates:
        return 0
    streak = 0
    check_date = date.today()
    for d_str in done_dates:
        d = date.fromisoformat(d_str)
        if d == check_date:
            streak += 1
            check_date -= timedelta(days=1)
        elif d == check_date:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break
    return streak

def list_cmd(args):
    data = load_json(HABITS_FILE, {"habits": []})
    logs = load_json(LOGS_FILE, {"logs": []})
    streaks = load_json(STREAKS_FILE, {"streaks": {}})
    today = date.today().isoformat()
    print("Your Habits:")
    print(f" {'#':<3} {'Habit':<25} {'Time':<10} {'Streak':<8} {'Today':<8} {'Paused'}")
    for i, h in enumerate(data["habits"], 1):
        streak = streaks["streaks"].get(h["id"], 0)
        today_log = next((l for l in logs["logs"] if l["habit_id"] == h["id"] and l["date"] == today), None)
        today_status = f"[{today_log['status']}]" if today_log else "[ -- ]"
        paused = "[paused]" if h.get("paused") else ""
        print(f" {i:<3} {h['name']:<25} {h['time']:<10} {str(streak)+'d':<8} {today_status:<8} {paused}")

def stats_cmd(args):
    data = load_json(HABITS_FILE, {"habits": []})
    habit = find_habit(data["habits"], args.habit)
    logs = load_json(LOGS_FILE, {"logs": []})
    days = int(args.days) if args.days else 30
    today = date.today()
    period_start = today - timedelta(days=days - 1)
    period_logs = [
        l for l in logs["logs"]
        if l["habit_id"] == habit["id"]
        and date.fromisoformat(l["date"]) >= period_start
    ]
    done_count = sum(1 for l in period_logs if l["status"] == "done")
    total = days
    streak = compute_streak(habit["id"], logs["logs"])
    completion_rate = round(done_count / total * 100, 1) if total > 0 else 0.0
    result = {
        "habit": habit["name"],
        "habit_id": habit["id"],
        "days_analyzed": days,
        "current_streak": streak,
        "done_count": done_count,
        "total_days": total,
        "completion_rate_pct": completion_rate,
        "period_start": period_start.isoformat(),
        "period_end": today.isoformat(),
        "logs": period_logs,
    }
    print(json.dumps(result, indent=2))

def overview_cmd(args):
    data = load_json(HABITS_FILE, {"habits": []})
    logs = load_json(LOGS_FILE, {"logs": []})
    streaks = load_json(STREAKS_FILE, {"streaks": {}})
    today = date.today().isoformat()
    overview = []
    for h in data["habits"]:
        today_log = next((l for l in logs["logs"] if l["habit_id"] == h["id"] and l["date"] == today), None)
        overview.append({
            "id": h["id"],
            "name": h["name"],
            "time": h["time"],
            "days": h["days"],
            "paused": h.get("paused", False),
            "streak": streaks["streaks"].get(h["id"], 0),
            "today_status": today_log["status"] if today_log else None,
        })
    print(json.dumps({"overview": overview, "date": today}, indent=2))

def edit_cmd(args):
    data = load_json(HABITS_FILE, {"habits": []})
    habit = find_habit(data["habits"], args.habit)
    if args.name:
        habit["name"] = args.name
    if args.time:
        habit["time"] = parse_time(args.time)
    if args.days:
        habit["days"] = parse_days(args.days)
    save_json(HABITS_FILE, data)
    print(f"Updated habit: {habit['name']}")
    print(json.dumps(habit))

def pause_cmd(args):
    data = load_json(HABITS_FILE, {"habits": []})
    habit = find_habit(data["habits"], args.habit)
    habit["paused"] = True
    save_json(HABITS_FILE, data)
    print(f"Paused habit: {habit['name']}")

def resume_cmd(args):
    data = load_json(HABITS_FILE, {"habits": []})
    habit = find_habit(data["habits"], args.habit)
    habit["paused"] = False
    save_json(HABITS_FILE, data)
    print(f"Resumed habit: {habit['name']}")

def delete_cmd(args):
    data = load_json(HABITS_FILE, {"habits": []})
    habit = find_habit(data["habits"], args.habit)
    data["habits"] = [h for h in data["habits"] if h["id"] != habit["id"]]
    save_json(HABITS_FILE, data)
    print(f"Deleted habit: {habit['name']}")

def main():
    parser = argparse.ArgumentParser(prog="habit_tracker.py")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("init")

    p_add = sub.add_parser("add")
    p_add.add_argument("--name", required=True)
    p_add.add_argument("--time")
    p_add.add_argument("--days")

    p_log = sub.add_parser("log")
    p_log.add_argument("--habit", required=True)
    p_log.add_argument("--status", required=True)

    sub.add_parser("list")

    p_stats = sub.add_parser("stats")
    p_stats.add_argument("--habit", required=True)
    p_stats.add_argument("--days")

    sub.add_parser("overview")

    p_edit = sub.add_parser("edit")
    p_edit.add_argument("--habit", required=True)
    p_edit.add_argument("--name")
    p_edit.add_argument("--time")
    p_edit.add_argument("--days")

    p_pause = sub.add_parser("pause")
    p_pause.add_argument("--habit", required=True)

    p_resume = sub.add_parser("resume")
    p_resume.add_argument("--habit", required=True)

    p_delete = sub.add_parser("delete")
    p_delete.add_argument("--habit", required=True)

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        sys.exit(1)

    cmds = {
        "init": init_cmd,
        "add": add_cmd,
        "log": log_cmd,
        "list": list_cmd,
        "stats": stats_cmd,
        "overview": overview_cmd,
        "edit": edit_cmd,
        "pause": pause_cmd,
        "resume": resume_cmd,
        "delete": delete_cmd,
    }
    cmds[args.command](args)

if __name__ == "__main__":
    main()
'''

(scripts_dir / "habit_tracker.py").write_text(habit_tracker_py)

# ── reminder.py ────────────────────────────────────────────────────────────
reminder_py = r'''#!/usr/bin/env python3
"""reminder.py - Manage habit reminders."""
import argparse, json, sys
from pathlib import Path

DATA_DIR = Path.home() / ".habitchat"
REMINDERS_FILE = DATA_DIR / "reminders.json"
REMINDER_LOG = DATA_DIR / "reminders.log"

def load_json(path, default):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return default
    return default

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))

def setup_cmd(args):
    data = load_json(REMINDERS_FILE, {"reminders": []})
    habits_file = DATA_DIR / "habits.json"
    habits_data = load_json(habits_file, {"habits": []})
    habit = next((h for h in habits_data["habits"] if args.habit.lower() in h["name"].lower() or h["id"].startswith(args.habit)), None)
    if not habit:
        print(f"Habit not found: {args.habit}", file=sys.stderr)
        sys.exit(1)
    reminder = {"habit_id": habit["id"], "habit_name": habit["name"], "time": habit["time"], "active": True}
    data["reminders"].append(reminder)
    save_json(REMINDERS_FILE, data)
    REMINDER_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(REMINDER_LOG, "a") as f:
        f.write(f"Reminder set for: {habit['name']} at {habit['time']}\n")
    print(f"Reminder set for {habit['name']} at {habit['time']}")

def list_cmd(args):
    data = load_json(REMINDERS_FILE, {"reminders": []})
    print(json.dumps(data, indent=2))

def disable_cmd(args):
    data = load_json(REMINDERS_FILE, {"reminders": []})
    for r in data["reminders"]:
        if args.habit.lower() in r["habit_name"].lower():
            r["active"] = False
    save_json(REMINDERS_FILE, data)
    print(f"Disabled reminder for {args.habit}")

def main():
    parser = argparse.ArgumentParser(prog="reminder.py")
    sub = parser.add_subparsers(dest="command")
    p = sub.add_parser("setup"); p.add_argument("--habit", required=True)
    sub.add_parser("list")
    p2 = sub.add_parser("disable"); p2.add_argument("--habit", required=True)
    args = parser.parse_args()
    if args.command == "setup": setup_cmd(args)
    elif args.command == "list": list_cmd(args)
    elif args.command == "disable": disable_cmd(args)
    else: parser.print_help()

if __name__ == "__main__":
    main()
'''
(scripts_dir / "reminder.py").write_text(reminder_py)

# ── coach.py ───────────────────────────────────────────────────────────────
coach_py = r'''#!/usr/bin/env python3
"""coach.py - AI coaching insights."""
import argparse, json, sys
from pathlib import Path

DATA_DIR = Path.home() / ".habitchat"

def load_json(path, default):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return default
    return default

def insights_cmd(args):
    habits = load_json(DATA_DIR / "habits.json", {"habits": []})
    logs = load_json(DATA_DIR / "logs.json", {"logs": []})
    result = {"total_habits": len(habits["habits"]), "total_logs": len(logs["logs"]), "insights": ["Keep building those habits!", "Consistency is key."]}
    print(json.dumps(result, indent=2))

def motivate_cmd(args):
    print(json.dumps({"message": f"You can do it! Keep going with '{args.habit}'!"}, indent=2))

def analyze_cmd(args):
    habits = load_json(DATA_DIR / "habits.json", {"habits": []})
    logs = load_json(DATA_DIR / "logs.json", {"logs": []})
    print(json.dumps({"analysis": "Looking at patterns...", "days": args.days, "habits": len(habits["habits"])}, indent=2))

def main():
    parser = argparse.ArgumentParser(prog="coach.py")
    sub = parser.add_subparsers(dest="command")
    p = sub.add_parser("insights"); p.add_argument("--user-data")
    p2 = sub.add_parser("motivate"); p2.add_argument("--habit", required=True)
    p3 = sub.add_parser("analyze"); p3.add_argument("--days")
    args = parser.parse_args()
    if args.command == "insights": insights_cmd(args)
    elif args.command == "motivate": motivate_cmd(args)
    elif args.command == "analyze": analyze_cmd(args)
    else: parser.print_help()

if __name__ == "__main__":
    main()
'''
(scripts_dir / "coach.py").write_text(coach_py)

# ── Skill manifest ─────────────────────────────────────────────────────────
manifest = {
    "name": "habitchat",
    "version": "1.0.0",
    "baseDir": str(skill_dir),
    "scripts": {
        "habit_tracker": str(scripts_dir / "habit_tracker.py"),
        "reminder": str(scripts_dir / "reminder.py"),
        "coach": str(scripts_dir / "coach.py"),
    }
}
(skill_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))

# ── SKILL.md placed in workspace root so agent can discover it ─────────────
# (Not written here - agent must read from the actual SKILL.md provided to it)

# ── A small "task brief" JSON for the agent (business context only) ─────────
task_brief = {
    "requester": "Alex (remote wellness startup employee)",
    "description": "See the prompt for full details.",
    "skill_manifest": str(skill_dir / "manifest.json"),
}
(workspace / "task_brief.json").write_text(json.dumps(task_brief, indent=2))

print("Workspace initialized.")
print(f"Skill scripts at: {scripts_dir}")