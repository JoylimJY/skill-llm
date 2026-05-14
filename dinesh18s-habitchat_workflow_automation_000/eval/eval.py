#!/usr/bin/env python3
"""
Evaluation script for HabitChat onboarding task.
Checks that the agent correctly:
1. Initialized ~/.habitchat/
2. Added 4 habits with correct time/day parsing
3. Logged "Morning run" as done and "Meditation" as skip
4. Set up a reminder for "Morning run"
5. Ran stats for "Meditation" with --days 30
"""

import json
import sys
import os
from pathlib import Path
from datetime import date

checks = []

def check(name, passed, detail=""):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return passed

def load_json(path):
    return json.loads(Path(path).read_text())

# ── Paths ──
home = Path.home()
habitchat_dir = home / ".habitchat"
habits_file = habitchat_dir / "habits.json"
logs_file = habitchat_dir / "logs.json"
streaks_file = habitchat_dir / "streaks.json"
config_file = habitchat_dir / "config.json"
reminders_file = habitchat_dir / "reminders.json"
reminders_log = habitchat_dir / "reminders.log"

# ── Check 1: Initialization ──
try:
    init_ok = (
        habitchat_dir.exists() and
        habits_file.exists() and
        logs_file.exists() and
        config_file.exists()
    )
    check("habitchat_initialized", init_ok,
          f"~/.habitchat/ exists={habitchat_dir.exists()}, "
          f"habits.json={habits_file.exists()}, logs.json={logs_file.exists()}, "
          f"config.json={config_file.exists()}")
except Exception as e:
    check("habitchat_initialized", False, f"Exception: {e}")

# ── Load habits ──
habits = []
try:
    data = load_json(habits_file)
    habits = data.get("habits", [])
    check("habits_file_valid_json", True, f"Loaded {len(habits)} habits")
except Exception as e:
    check("habits_file_valid_json", False, f"Exception reading habits.json: {e}")

# ── Helper: find habit by name fragment ──
def find_habit(name_fragment):
    for h in habits:
        if name_fragment.lower() in h.get("name", "").lower():
            return h
    return None

# ── Check 2: Morning run added with correct time and weekdays ──
try:
    h = find_habit("morning run")
    if h is None:
        check("habit_morning_run_added", False, "No habit matching 'morning run' found")
    else:
        # time must be "06:30"
        time_ok = h.get("time", "") == "06:30"
        # days must be exactly "mon,tue,wed,thu,fri" (weekdays)
        days_val = h.get("days", "")
        # Accept any ordering as long as it contains exactly mon,tue,wed,thu,fri
        days_set = set(d.strip() for d in days_val.split(","))
        days_ok = days_set == {"mon", "tue", "wed", "thu", "fri"}
        passed = time_ok and days_ok
        check("habit_morning_run_added", passed,
              f"name='{h.get('name')}' time='{h.get('time')}' (expected '06:30') "
              f"days='{days_val}' (expected 'mon,tue,wed,thu,fri') "
              f"time_ok={time_ok} days_ok={days_ok}")
except Exception as e:
    check("habit_morning_run_added", False, f"Exception: {e}")

# ── Check 3: Meditation added with time "09:00" and all days ──
try:
    h = find_habit("meditation")
    if h is None:
        check("habit_meditation_added", False, "No habit matching 'meditation' found")
    else:
        time_ok = h.get("time", "") == "09:00"
        days_val = h.get("days", "")
        days_set = set(d.strip() for d in days_val.split(","))
        # All 7 days
        days_ok = days_set == {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}
        passed = time_ok and days_ok
        check("habit_meditation_added", passed,
              f"name='{h.get('name')}' time='{h.get('time')}' (expected '09:00') "
              f"days='{days_val}' (expected all 7 days) "
              f"time_ok={time_ok} days_ok={days_ok}")
except Exception as e:
    check("habit_meditation_added", False, f"Exception: {e}")

# ── Check 4: Evening reading added with time "19:00" and all days ──
try:
    h = find_habit("read")
    if h is None:
        check("habit_reading_added", False, "No habit matching 'read' found")
    else:
        time_ok = h.get("time", "") == "19:00"
        days_val = h.get("days", "")
        days_set = set(d.strip() for d in days_val.split(","))
        days_ok = days_set == {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}
        passed = time_ok and days_ok
        check("habit_reading_added", passed,
              f"name='{h.get('name')}' time='{h.get('time')}' (expected '19:00') "
              f"days='{days_val}' (expected all 7 days) "
              f"time_ok={time_ok} days_ok={days_ok}")
except Exception as e:
    check("habit_reading_added", False, f"Exception: {e}")

# ── Check 5: Water habit added ──
try:
    h = find_habit("water")
    if h is None:
        check("habit_water_added", False, "No habit matching 'water' found")
    else:
        days_val = h.get("days", "")
        days_set = set(d.strip() for d in days_val.split(","))
        days_ok = days_set == {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}
        check("habit_water_added", days_ok,
              f"name='{h.get('name')}' days='{days_val}' days_ok={days_ok}")
except Exception as e:
    check("habit_water_added", False, f"Exception: {e}")

# ── Load logs ──
logs = []
try:
    log_data = load_json(logs_file)
    logs = log_data.get("logs", [])
    check("logs_file_valid_json", True, f"Loaded {len(logs)} log entries")
except Exception as e:
    check("logs_file_valid_json", False, f"Exception reading logs.json: {e}")

today = date.today().isoformat()

# ── Helper: find log for habit by name fragment ──
def find_log(name_fragment, status=None):
    # First get habit id
    h = find_habit(name_fragment)
    if not h:
        return None
    for log in logs:
        if log.get("habit_id") == h.get("id") and log.get("date") == today:
            if status is None or log.get("status") == status:
                return log
    return None

# ── Check 6: Morning run logged as "done" today ──
try:
    h = find_habit("morning run")
    if h is None:
        check("morning_run_logged_done", False, "Habit 'morning run' not found, cannot check log")
    else:
        today_logs = [l for l in logs
                      if l.get("habit_id") == h.get("id") and l.get("date") == today and l.get("status") == "done"]
        passed = len(today_logs) > 0
        check("morning_run_logged_done", passed,
              f"Found {len(today_logs)} 'done' log(s) for 'morning run' on {today}")
except Exception as e:
    check("morning_run_logged_done", False, f"Exception: {e}")

# ── Check 7: Meditation logged as "skip" today ──
try:
    h = find_habit("meditation")
    if h is None:
        check("meditation_logged_skip", False, "Habit 'meditation' not found, cannot check log")
    else:
        today_logs = [l for l in logs
                      if l.get("habit_id") == h.get("id") and l.get("date") == today and l.get("status") == "skip"]
        passed = len(today_logs) > 0
        check("meditation_logged_skip", passed,
              f"Found {len(today_logs)} 'skip' log(s) for 'meditation' on {today}")
except Exception as e:
    check("meditation_logged_skip", False, f"Exception: {e}")

# ── Check 8: Reminder set up for Morning run ──
try:
    reminder_found = False
    detail = ""
    if reminders_file.exists():
        rem_data = load_json(reminders_file)
        reminders = rem_data.get("reminders", [])
        h = find_habit("morning run")
        if h:
            for r in reminders:
                if r.get("habit_id") == h.get("id") and r.get("enabled", False):
                    reminder_found = True
                    detail = f"Reminder found: habit_id={r.get('habit_id')} time={r.get('time')} enabled={r.get('enabled')}"
                    break
        if not reminder_found:
            detail = f"reminders.json exists but no enabled reminder for 'morning run'. Reminders: {reminders}"
    elif reminders_log.exists():
        # Fallback: check the reminders.log
        log_content = reminders_log.read_text()
        if "morning run" in log_content.lower() or "Morning run" in log_content:
            reminder_found = True
            detail = f"Found in reminders.log: {log_content[:200]}"
        else:
            detail = f"reminders.log exists but 'morning run' not found. Content: {log_content[:200]}"
    else:
        detail = "Neither reminders.json nor reminders.log found"
    check("reminder_setup_morning_run", reminder_found, detail)
except Exception as e:
    check("reminder_setup_morning_run", False, f"Exception: {e}")

# ── Check 9: Stats were run for Meditation (streaks.json or stats output artifact) ──
# Since stats prints to stdout and doesn't write a file, we check that streaks.json
# has an entry for meditation (which gets updated when logs are written),
# OR check that the habit exists with a log (stats requires habit to exist).
# The real trap is: did they use --days 30?
# We can't directly verify --days 30 was passed, but we can verify that the meditation
# habit exists and has been logged (prerequisite for meaningful stats).
try:
    h = find_habit("meditation")
    streaks_ok = False
    detail = ""
    if streaks_file.exists():
        streak_data = load_json(streaks_file)
        streaks = streak_data.get("streaks", {})
        if h and h.get("id") in streaks:
            streaks_ok = True
            detail = f"Streak entry found for meditation: {streaks[h.get('id')]}"
        else:
            detail = f"Streaks file exists but no entry for meditation id={h.get('id') if h else 'N/A'}. Keys: {list(streaks.keys())}"
    else:
        detail = "streaks.json does not exist"
    check("stats_ran_for_meditation", streaks_ok, detail)
except Exception as e:
    check("stats_ran_for_meditation", False, f"Exception: {e}")

# ── Check 10: Exactly 4 habits were added (not more, not fewer) ──
try:
    n = len(habits)
    passed = n == 4
    check("exactly_4_habits_added", passed, f"Found {n} habits (expected 4): {[h.get('name') for h in habits]}")
except Exception as e:
    check("exactly_4_habits_added", False, f"Exception: {e}")

# ── Final scoring ──
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 3) if total > 0 else 0.0
overall_passed = passed_count == total

result = {
    "passed": overall_passed,
    "score": score,
    "checks": checks
}

print(json.dumps(result, indent=2))