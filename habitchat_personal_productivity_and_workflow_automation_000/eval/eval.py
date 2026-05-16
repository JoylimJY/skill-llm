#!/usr/bin/env python3
"""
Evaluation script for the HabitChat multi-step task.

Expected agent actions (in order):
1. Run habit_tracker.py init  →  creates ~/.habitchat/
2. Add habit "Morning meditation" at 06:30, all days
3. Add habit "Evening run" at "evening" (→ 19:00), weekdays (→ mon,tue,wed,thu,fri)
4. Add habit "Read 30 minutes" at 21:00, weekends (→ sat,sun)
5. Log "Morning meditation" as done
6. Log "Evening run" as skip
7. Log "Read 30 minutes" as miss
8. Edit "Evening run" → rename to "Evening jog", change time to 18:30
9. Pause "Read 30 minutes"
10. Run stats for "Morning meditation" with --days 7
"""

import sys
import json
import subprocess
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
home = Path.home()
habitchat_dir = home / ".habitchat"

checks = []

def check(name, condition, detail):
    checks.append({"name": name, "passed": bool(condition), "detail": detail})
    return bool(condition)

# ── CHECK 1: ~/.habitchat/ initialized ────────────────────────────────────
try:
    init_ok = (
        habitchat_dir.exists() and
        (habitchat_dir / "habits.json").exists() and
        (habitchat_dir / "logs.json").exists() and
        (habitchat_dir / "config.json").exists()
    )
    check("init_directory", init_ok, f"~/.habitchat/ exists with required JSON files: {init_ok}")
except Exception as e:
    check("init_directory", False, f"Exception: {e}")

# ── Load habits ────────────────────────────────────────────────────────────
try:
    habits_data = json.loads((habitchat_dir / "habits.json").read_text())
    habits_list = habits_data.get("habits", [])
except Exception as e:
    habits_list = []
    check("habits_file_readable", False, f"Could not read habits.json: {e}")

def find_habit_by_name_fragment(fragment):
    fragment = fragment.lower()
    for h in habits_list:
        if fragment in h["name"].lower():
            return h
    return None

# ── CHECK 2: "Morning meditation" added with correct time ─────────────────
try:
    med = find_habit_by_name_fragment("morning meditation")
    if med:
        time_ok = med.get("time") == "06:30"
        days_ok = set(med.get("days", [])) == {"mon","tue","wed","thu","fri","sat","sun"}
        check("habit_morning_meditation_time", time_ok,
              f"Expected time=06:30, got {med.get('time')}")
        check("habit_morning_meditation_days", days_ok,
              f"Expected all 7 days, got {med.get('days')}")
    else:
        check("habit_morning_meditation_time", False, "Habit 'Morning meditation' not found")
        check("habit_morning_meditation_days", False, "Habit 'Morning meditation' not found")
except Exception as e:
    check("habit_morning_meditation_time", False, f"Exception: {e}")
    check("habit_morning_meditation_days", False, f"Exception: {e}")

# ── CHECK 3: "Evening run" or "Evening jog" — weekdays + evening parse ─────
# After editing, name should be "Evening jog" with time 18:30
# But we must also verify the original was added with time=19:00 and days=weekdays
# We check the FINAL state: renamed to "Evening jog" at 18:30, weekdays
try:
    jog = find_habit_by_name_fragment("evening jog")
    run = find_habit_by_name_fragment("evening run")
    target = jog if jog else run
    if target:
        # After edit: should be "Evening jog"
        name_edited = target.get("name", "").lower() == "evening jog"
        time_edited = target.get("time") == "18:30"
        days_weekdays = set(target.get("days", [])) == {"mon","tue","wed","thu","fri"}
        check("habit_evening_jog_renamed", name_edited,
              f"Expected name='Evening jog', got '{target.get('name')}'")
        check("habit_evening_jog_time_edited", time_edited,
              f"Expected time=18:30 after edit, got {target.get('time')}")
        check("habit_evening_jog_days", days_weekdays,
              f"Expected weekdays (mon-fri), got {target.get('days')}")
    else:
        check("habit_evening_jog_renamed", False, "Neither 'Evening jog' nor 'Evening run' found")
        check("habit_evening_jog_time_edited", False, "Habit not found")
        check("habit_evening_jog_days", False, "Habit not found")
except Exception as e:
    check("habit_evening_jog_renamed", False, f"Exception: {e}")
    check("habit_evening_jog_time_edited", False, f"Exception: {e}")
    check("habit_evening_jog_days", False, f"Exception: {e}")

# ── CHECK 4: "Read 30 minutes" — weekends + paused ────────────────────────
try:
    read = find_habit_by_name_fragment("read")
    if read:
        days_weekends = set(read.get("days", [])) == {"sat", "sun"}
        is_paused = read.get("paused") is True
        check("habit_read_days_weekends", days_weekends,
              f"Expected sat,sun only, got {read.get('days')}")
        check("habit_read_paused", is_paused,
              f"Expected paused=True, got {read.get('paused')}")
    else:
        check("habit_read_days_weekends", False, "Habit 'Read 30 minutes' not found")
        check("habit_read_paused", False, "Habit 'Read 30 minutes' not found")
except Exception as e:
    check("habit_read_days_weekends", False, f"Exception: {e}")
    check("habit_read_paused", False, f"Exception: {e}")

# ── CHECK 5: Logs ──────────────────────────────────────────────────────────
try:
    logs_data = json.loads((habitchat_dir / "logs.json").read_text())
    logs_list = logs_data.get("logs", [])

    def find_log(habit_fragment, status):
        habit = find_habit_by_name_fragment(habit_fragment)
        if not habit:
            return None
        return next((l for l in logs_list if l["habit_id"] == habit["id"] and l["status"] == status), None)

    med_log = find_log("morning meditation", "done")
    check("log_morning_meditation_done", med_log is not None,
          f"Expected morning meditation logged as 'done'. Found: {med_log}")

    # evening run/jog logged as skip
    jog2 = jog if jog else run
    skip_log = None
    if jog2:
        skip_log = next((l for l in logs_list if l["habit_id"] == jog2["id"] and l["status"] == "skip"), None)
    check("log_evening_run_skip", skip_log is not None,
          f"Expected Evening run/jog logged as 'skip'. Found: {skip_log}")

    read_miss = None
    if read:
        read_miss = next((l for l in logs_list if l["habit_id"] == read["id"] and l["status"] == "miss"), None)
    check("log_read_miss", read_miss is not None,
          f"Expected 'Read 30 minutes' logged as 'miss'. Found: {read_miss}")

except Exception as e:
    check("log_morning_meditation_done", False, f"Exception reading logs: {e}")
    check("log_evening_run_skip", False, f"Exception reading logs: {e}")
    check("log_read_miss", False, f"Exception reading logs: {e}")

# ── CHECK 6: Stats command was run for Morning meditation --days 7 ─────────
# We can't easily verify that the command was run, but we can verify the streak
# was computed (streaks.json updated) and data is consistent
try:
    streaks_data = json.loads((habitchat_dir / "streaks.json").read_text())
    streaks = streaks_data.get("streaks", {})
    med = find_habit_by_name_fragment("morning meditation")
    if med:
        streak_val = streaks.get(med["id"])
        # After one "done" log today, streak should be >= 1
        streak_ok = streak_val is not None and streak_val >= 1
        check("streaks_morning_meditation_computed", streak_ok,
              f"Expected streak >= 1 for morning meditation after done log. Got: {streak_val}")
    else:
        check("streaks_morning_meditation_computed", False, "Habit not found for streak check")
except Exception as e:
    check("streaks_morning_meditation_computed", False, f"Exception reading streaks: {e}")

# ── CHECK 7: Read habit time is 21:00 (before any edits to other habits) ──
try:
    read2 = find_habit_by_name_fragment("read")
    if read2:
        time_read_ok = read2.get("time") == "21:00"
        check("habit_read_time_2100", time_read_ok,
              f"Expected 'Read 30 minutes' time=21:00, got {read2.get('time')}")
    else:
        check("habit_read_time_2100", False, "Read habit not found")
except Exception as e:
    check("habit_read_time_2100", False, f"Exception: {e}")

# ── Scoring ────────────────────────────────────────────────────────────────
passed_count = sum(1 for c in checks if c["passed"])
total = len(checks)
score = round(passed_count / total, 3) if total > 0 else 0.0
all_passed = passed_count == total

result = {
    "passed": all_passed,
    "score": score,
    "checks": checks,
}
print(json.dumps(result, indent=2))