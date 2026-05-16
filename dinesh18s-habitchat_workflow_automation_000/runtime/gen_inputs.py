import os
import json
import stat
import random
import string
import textwrap
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── Skill directory structure (mimicking a real openclaw skill install) ──
skill_base = workspace / "skills" / "habitchat"
scripts_dir = skill_base / "scripts"
scripts_dir.mkdir(parents=True, exist_ok=True)

# ── Distractor files ──
distractor_dirs = [
    workspace / "projects" / "alpha",
    workspace / "projects" / "beta",
    workspace / "notes" / "2024",
    workspace / "notes" / "2025",
    workspace / "config" / "system",
    workspace / "config" / "user",
    workspace / "logs" / "app",
    workspace / "tmp" / "cache",
    workspace / "archive" / "old_habits",
    workspace / "archive" / "exports",
]
for d in distractor_dirs:
    d.mkdir(parents=True, exist_ok=True)

distractor_files = {
    workspace / "projects" / "alpha" / "plan.md": "# Alpha Project\nDeadlines and tasks go here.",
    workspace / "projects" / "beta" / "notes.txt": "Beta project notes - nothing useful here.",
    workspace / "notes" / "2024" / "january.txt": "Old notes from January 2024.",
    workspace / "notes" / "2025" / "goals.txt": "Lose weight, read more, meditate.",
    workspace / "config" / "system" / "prefs.json": json.dumps({"theme": "dark", "lang": "en"}),
    workspace / "config" / "user" / "shortcuts.json": json.dumps({"open": "ctrl+o", "save": "ctrl+s"}),
    workspace / "logs" / "app" / "error.log": "2025-01-01 ERROR: something failed\n2025-01-02 INFO: ok",
    workspace / "tmp" / "cache" / "dummy.bin": "binary-like-content-xyz",
    workspace / "archive" / "old_habits" / "habits_2023.json": json.dumps({
        "habits": [
            {"name": "Old Yoga", "time": "07:00", "days": "mon,wed,fri"},
            {"name": "Journal", "time": "22:00", "days": "mon,tue,wed,thu,fri,sat,sun"}
        ]
    }),
    workspace / "archive" / "exports" / "export_2024.csv": "date,habit,status\n2024-01-01,yoga,done\n2024-01-02,yoga,miss",
    workspace / "notes" / "2025" / "wellness_plan.txt": textwrap.dedent("""\
        Alex's 30-Day Wellness Challenge Plan
        ======================================
        Habits to track:
        1. Morning run - every weekday at 6:30am
        2. Meditation - every day at 9am
        3. Evening reading - every day, evening time
        4. Drink water (8 glasses) - all day, every day

        Alex needs reminders set up for Morning run.
        After setup, log Morning run as done for today.
        Also log Meditation as skipped for today.
        Then check stats for Meditation over the last 30 days.
    """),
}

for path, content in distractor_files.items():
    path.write_text(content)

# ── habit_tracker.py (the main script) ──
habit_tracker_py = scripts_dir / "habit_tracker.py"
habit_tracker_py.write_text(textwrap.dedent('''\
#!/usr/bin/env python3
"""
HabitChat habit tracker - local data management script.
All data stored in ~/.habitchat/
"""

import argparse
import json
import os
import sys
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

DATA_DIR = Path.home() / ".habitchat"
HABITS_FILE = DATA_DIR / "habits.json"
LOGS_FILE = DATA_DIR / "logs.json"
STREAKS_FILE = DATA_DIR / "streaks.json"
CONFIG_FILE = DATA_DIR / "config.json"


def ensure_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_json(path, default):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return default
    return default


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2))


def short_id():
    return str(uuid.uuid4())[:8]


def cmd_init(args):
    ensure_dir()
    if not HABITS_FILE.exists():
        save_json(HABITS_FILE, {"habits": []})
    if not LOGS_FILE.exists():
        save_json(LOGS_FILE, {"logs": []})
    if not STREAKS_FILE.exists():
        save_json(STREAKS_FILE, {"streaks": {}})
    if not CONFIG_FILE.exists():
        save_json(CONFIG_FILE, {"timezone": "UTC", "coaching_style": "warm"})
    print("HabitChat initialized successfully.")


def find_habit(habits, name_or_id):
    for h in habits:
        if h["id"] == name_or_id or h["name"].lower() == name_or_id.lower():
            return h
    # partial match
    matches = [h for h in habits if name_or_id.lower() in h["name"].lower()]
    if len(matches) == 1:
        return matches[0]
    return None


def cmd_add(args):
    ensure_dir()
    data = load_json(HABITS_FILE, {"habits": []})
    habit = {
        "id": short_id(),
        "name": args.name,
        "time": args.time,
        "days": args.days,
        "active": True,
        "paused": False,
        "created": date.today().isoformat(),
    }
    data["habits"].append(habit)
    save_json(HABITS_FILE, data)
    print(f"Habit added: {habit['name']} (id: {habit['id']}) at {habit['time']} on {habit['days']}")


def cmd_log(args):
    ensure_dir()
    data = load_json(HABITS_FILE, {"habits": []})
    habit = find_habit(data["habits"], args.habit)
    if not habit:
        print(f"ERROR: Habit '{args.habit}' not found.", file=sys.stderr)
        sys.exit(1)
    logs = load_json(LOGS_FILE, {"logs": []})
    today = date.today().isoformat()
    # Remove existing log for today for this habit
    logs["logs"] = [l for l in logs["logs"]
                    if not (l["habit_id"] == habit["id"] and l["date"] == today)]
    logs["logs"].append({
        "habit_id": habit["id"],
        "habit_name": habit["name"],
        "date": today,
        "status": args.status,
        "logged_at": datetime.now().isoformat(),
    })
    save_json(LOGS_FILE, logs)
    # Compute streak
    streaks = load_json(STREAKS_FILE, {"streaks": {}})
    all_done = sorted(
        [l["date"] for l in logs["logs"]
         if l["habit_id"] == habit["id"] and l["status"] == "done"],
        reverse=True
    )
    streak = 0
    check = date.today()
    for d in all_done:
        if date.fromisoformat(d) == check:
            streak += 1
            check -= timedelta(days=1)
        else:
            break
    streaks["streaks"][habit["id"]] = {"current": streak, "habit_name": habit["name"]}
    save_json(STREAKS_FILE, streaks)
    print(f"Logged {habit['name']} as {args.status} for {today}. Current streak: {streak} day(s).")


def cmd_list(args):
    data = load_json(HABITS_FILE, {"habits": []})
    logs = load_json(LOGS_FILE, {"logs": []})
    today = date.today().isoformat()
    print("Your Habits:")
    print(f" {'#':<3} {'Habit':<25} {'Time':<10} {'Days':<30} {'Today':<8}")
    for i, h in enumerate(data["habits"], 1):
        today_logs = [l for l in logs["logs"] if l["habit_id"] == h["id"] and l["date"] == today]
        status = today_logs[0]["status"] if today_logs else "--"
        print(f" {i:<3} {h['name']:<25} {h['time']:<10} {h['days']:<30} [{status}]")


def cmd_stats(args):
    data = load_json(HABITS_FILE, {"habits": []})
    habit = find_habit(data["habits"], args.habit)
    if not habit:
        print(f"ERROR: Habit '{args.habit}' not found.", file=sys.stderr)
        sys.exit(1)
    logs = load_json(LOGS_FILE, {"logs": []})
    days = args.days if args.days else 30
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    relevant = [l for l in logs["logs"]
                if l["habit_id"] == habit["id"] and l["date"] >= cutoff]
    done_count = sum(1 for l in relevant if l["status"] == "done")
    total = len(relevant)
    streaks = load_json(STREAKS_FILE, {"streaks": {}})
    current_streak = streaks.get("streaks", {}).get(habit["id"], {}).get("current", 0)
    pct = int(done_count / total * 100) if total > 0 else 0
    print(f"Stats for: {habit['name']}")
    print(f"  Period: last {days} days")
    print(f"  Completed: {done_count}/{total} ({pct}%)")
    print(f"  Current streak: {current_streak} day(s)")


def cmd_overview(args):
    data = load_json(HABITS_FILE, {"habits": []})
    logs = load_json(LOGS_FILE, {"logs": []})
    streaks = load_json(STREAKS_FILE, {"streaks": {}})
    today = date.today().isoformat()
    print("=== HabitChat Overview ===")
    for h in data["habits"]:
        today_logs = [l for l in logs["logs"] if l["habit_id"] == h["id"] and l["date"] == today]
        status = today_logs[0]["status"] if today_logs else "pending"
        streak = streaks.get("streaks", {}).get(h["id"], {}).get("current", 0)
        paused = " [PAUSED]" if h.get("paused") else ""
        print(f"  {h['name']}{paused}: today={status}, streak={streak}d")


def cmd_edit(args):
    data = load_json(HABITS_FILE, {"habits": []})
    habit = find_habit(data["habits"], args.habit)
    if not habit:
        print(f"ERROR: Habit '{args.habit}' not found.", file=sys.stderr)
        sys.exit(1)
    if args.name:
        habit["name"] = args.name
    if args.time:
        habit["time"] = args.time
    if args.days:
        habit["days"] = args.days
    save_json(HABITS_FILE, data)
    print(f"Habit updated: {habit['name']}")


def cmd_pause(args):
    data = load_json(HABITS_FILE, {"habits": []})
    habit = find_habit(data["habits"], args.habit)
    if not habit:
        print(f"ERROR: Habit '{args.habit}' not found.", file=sys.stderr)
        sys.exit(1)
    habit["paused"] = True
    save_json(HABITS_FILE, data)
    print(f"Habit paused: {habit['name']}")


def cmd_resume(args):
    data = load_json(HABITS_FILE, {"habits": []})
    habit = find_habit(data["habits"], args.habit)
    if not habit:
        print(f"ERROR: Habit '{args.habit}' not found.", file=sys.stderr)
        sys.exit(1)
    habit["paused"] = False
    save_json(HABITS_FILE, data)
    print(f"Habit resumed: {habit['name']}")


def cmd_delete(args):
    data = load_json(HABITS_FILE, {"habits": []})
    habit = find_habit(data["habits"], args.habit)
    if not habit:
        print(f"ERROR: Habit '{args.habit}' not found.", file=sys.stderr)
        sys.exit(1)
    data["habits"] = [h for h in data["habits"] if h["id"] != habit["id"]]
    save_json(HABITS_FILE, data)
    print(f"Habit deleted: {habit['name']}")


def main():
    parser = argparse.ArgumentParser(description="HabitChat Tracker")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("init")

    p_add = sub.add_parser("add")
    p_add.add_argument("--name", required=True)
    p_add.add_argument("--time", required=True)
    p_add.add_argument("--days", required=True)

    p_log = sub.add_parser("log")
    p_log.add_argument("--habit", required=True)
    p_log.add_argument("--status", required=True, choices=["done", "skip", "miss"])

    sub.add_parser("list")

    p_stats = sub.add_parser("stats")
    p_stats.add_argument("--habit", required=True)
    p_stats.add_argument("--days", type=int, default=30)

    sub.add_parser("overview")

    p_edit = sub.add_parser("edit")
    p_edit.add_argument("--habit", required=True)
    p_edit.add_argument("--name", default=None)
    p_edit.add_argument("--time", default=None)
    p_edit.add_argument("--days", default=None)

    p_pause = sub.add_parser("pause")
    p_pause.add_argument("--habit", required=True)

    p_resume = sub.add_parser("resume")
    p_resume.add_argument("--habit", required=True)

    p_delete = sub.add_parser("delete")
    p_delete.add_argument("--habit", required=True)

    args = parser.parse_args()
    cmds = {
        "init": cmd_init,
        "add": cmd_add,
        "log": cmd_log,
        "list": cmd_list,
        "stats": cmd_stats,
        "overview": cmd_overview,
        "edit": cmd_edit,
        "pause": cmd_pause,
        "resume": cmd_resume,
        "delete": cmd_delete,
    }
    if args.command in cmds:
        cmds[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
'''))

# ── reminder.py ──
reminder_py = scripts_dir / "reminder.py"
reminder_py.write_text(textwrap.dedent('''\
#!/usr/bin/env python3
"""
HabitChat reminder manager.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

DATA_DIR = Path.home() / ".habitchat"
HABITS_FILE = DATA_DIR / "habits.json"
REMINDERS_LOG = DATA_DIR / "reminders.log"
REMINDERS_FILE = DATA_DIR / "reminders.json"


def load_json(path, default):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return default
    return default


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2))


def find_habit(habits, name_or_id):
    for h in habits:
        if h["id"] == name_or_id or h["name"].lower() == name_or_id.lower():
            return h
    matches = [h for h in habits if name_or_id.lower() in h["name"].lower()]
    if len(matches) == 1:
        return matches[0]
    return None


def cmd_setup(args):
    data = load_json(HABITS_FILE, {"habits": []})
    habit = find_habit(data["habits"], args.habit)
    if not habit:
        print(f"ERROR: Habit \\'{args.habit}\\' not found.", file=sys.stderr)
        sys.exit(1)
    reminders = load_json(REMINDERS_FILE, {"reminders": []})
    # Remove existing reminder for this habit
    reminders["reminders"] = [r for r in reminders["reminders"] if r["habit_id"] != habit["id"]]
    reminders["reminders"].append({
        "habit_id": habit["id"],
        "habit_name": habit["name"],
        "time": habit["time"],
        "enabled": True,
        "created": datetime.now().isoformat(),
    })
    save_json(REMINDERS_FILE, reminders)
    # Write to log as fallback
    with open(REMINDERS_LOG, "a") as f:
        f.write(f"{datetime.now().isoformat()} SETUP reminder for {habit[\\'name\\']} at {habit[\\'time\\']}\\n")
    print(f"Reminder set up for: {habit[\\'name\\']} at {habit[\\'time\\']}")


def cmd_list(args):
    reminders = load_json(REMINDERS_FILE, {"reminders": []})
    if not reminders["reminders"]:
        print("No active reminders.")
        return
    print("Active Reminders:")
    for r in reminders["reminders"]:
        status = "enabled" if r.get("enabled") else "disabled"
        print(f"  {r[\\'habit_name\\']} at {r[\\'time\\']} [{status}]")


def cmd_disable(args):
    data = load_json(HABITS_FILE, {"habits": []})
    habit = find_habit(data["habits"], args.habit)
    if not habit:
        print(f"ERROR: Habit \\'{args.habit}\\' not found.", file=sys.stderr)
        sys.exit(1)
    reminders = load_json(REMINDERS_FILE, {"reminders": []})
    for r in reminders["reminders"]:
        if r["habit_id"] == habit["id"]:
            r["enabled"] = False
    save_json(REMINDERS_FILE, reminders)
    print(f"Reminder disabled for: {habit[\\'name\\']}")


def main():
    parser = argparse.ArgumentParser(description="HabitChat Reminder Manager")
    sub = parser.add_subparsers(dest="command")

    p_setup = sub.add_parser("setup")
    p_setup.add_argument("--habit", required=True)

    sub.add_parser("list")

    p_disable = sub.add_parser("disable")
    p_disable.add_argument("--habit", required=True)

    args = parser.parse_args()
    cmds = {
        "setup": cmd_setup,
        "list": cmd_list,
        "disable": cmd_disable,
    }
    if args.command in cmds:
        cmds[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
'''))

# ── coach.py ──
coach_py = scripts_dir / "coach.py"
coach_py.write_text(textwrap.dedent('''\
#!/usr/bin/env python3
"""
HabitChat AI coaching script.
"""

import argparse
import json
from pathlib import Path

DATA_DIR = Path.home() / ".habitchat"


def load_json(path, default):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return default
    return default


def cmd_insights(args):
    habits = load_json(DATA_DIR / "habits.json", {"habits": []})
    logs = load_json(DATA_DIR / "logs.json", {"logs": []})
    print(f"Coaching insights based on {len(habits[\'habits\'])} habits and {len(logs[\'logs\'])} log entries.")
    for h in habits["habits"]:
        done = sum(1 for l in logs["logs"] if l["habit_id"] == h["id"] and l["status"] == "done")
        print(f"  {h[\'name\']}: {done} completed sessions")


def cmd_motivate(args):
    habits = load_json(DATA_DIR / "habits.json", {"habits": []})
    match = next((h for h in habits["habits"] if args.habit.lower() in h["name"].lower()), None)
    if match:
        print(f"Keep going with {match[\'name\']}! Every day counts.")
    else:
        print("Keep building those habits!")


def cmd_analyze(args):
    logs = load_json(DATA_DIR / "logs.json", {"logs": []})
    print(f"Analysis over last {args.days} days: {len(logs[\'logs\'])} total log entries.")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")

    p_insights = sub.add_parser("insights")
    p_insights.add_argument("--user-data", default=str(DATA_DIR))

    p_motivate = sub.add_parser("motivate")
    p_motivate.add_argument("--habit", required=True)

    p_analyze = sub.add_parser("analyze")
    p_analyze.add_argument("--days", type=int, default=30)

    args = parser.parse_args()
    cmds = {"insights": cmd_insights, "motivate": cmd_motivate, "analyze": cmd_analyze}
    if args.command in cmds:
        cmds[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
'''))

# ── SKILL.md in the skill directory ──
skill_md = skill_base / "SKILL.md"
skill_md.write_text(Path("/workspace/SKILL.md").read_text() if Path("/workspace/SKILL.md").exists() else "# HabitChat Skill")

# ── A fake task brief (part of the distractor set) ──
(workspace / "notes" / "2025" / "task_brief.txt").write_text(textwrap.dedent("""\
    Task for onboarding assistant:
    Bootstrap Alex's habit tracking. See wellness_plan.txt for details.
    The skill scripts live under skills/habitchat/scripts/.
"""))

print("Workspace generated successfully.")
print(f"Skill scripts at: {scripts_dir}")
print(f"Distractor files: {len(distractor_files)}")