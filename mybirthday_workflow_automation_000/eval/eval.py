#!/usr/bin/env python3
"""
Evaluation script for member-manager task.
Usage: python3 eval_script.py /workspace
"""
import sys
import json
import os
import re
from datetime import date, timedelta
from pathlib import Path

# ── helpers ───────────────────────────────────────────────────────────────────
def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

checks = []

def check(name, passed, detail=""):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return passed

# ── paths ─────────────────────────────────────────────────────────────────────
SESSION_KEY   = "telegram_88291047"
BASE_DIR      = os.path.expanduser(f"~/.openclaw/workspace/users/{SESSION_KEY}")
MEMBERS_PATH  = os.path.join(BASE_DIR, "members.json")
REMINDERS_PATH= os.path.join(BASE_DIR, "reminders.json")
TASKS_FILE    = "/tmp/mock_scheduled_tasks.json"

# ── Check 1: correct session key directory used ───────────────────────────────
try:
    members = load_json(MEMBERS_PATH)
    check("correct_session_directory",
          True,
          f"members.json exists at {MEMBERS_PATH}")
except Exception as e:
    check("correct_session_directory", False,
          f"Cannot read {MEMBERS_PATH}: {e}")
    members = []

# Verify the WRONG "default" directory was NOT used as the primary store
try:
    default_members = load_json(
        os.path.expanduser("~/.openclaw/workspace/users/default/members.json")
    )
    # If default has MORE members than just the decoy, something is wrong
    decoy_only = all(m.get("name") == "陷阱成員" for m in default_members)
    check("did_not_use_default_directory",
          decoy_only,
          "default/ directory should only contain the pre-planted decoy member")
except Exception:
    check("did_not_use_default_directory", True,
          "default/ directory unmodified (or unreadable) — acceptable")

# ── Check 2: Two required members present ─────────────────────────────────────
REQUIRED_MEMBERS = [
    {"name": "阿嬤", "group": "家庭"},   # Grandma — lunar birthday
    {"name": "大舅", "group": "親戚"},   # Uncle — lunar birthday
]

def find_member(members, name, group):
    for m in members:
        if m.get("name") == name and m.get("group") == group:
            return m
    return None

granny   = find_member(members, "阿嬤", "家庭")
uncle    = find_member(members, "大舅", "親戚")

check("member_granny_exists",
      granny is not None,
      f"阿嬤 (家庭) found: {granny is not None}")
check("member_uncle_exists",
      uncle is not None,
      f"大舅 (親戚) found: {uncle is not None}")

# ── Check 3: Lunar birthday stored correctly ──────────────────────────────────
# 阿嬤: lunar 七月初七 (month=7, day=7)
if granny:
    lb = granny.get("birthday_lunar") or {}
    lunar_ok = (int(lb.get("month", 0)) == 7 and int(lb.get("day", 0)) == 7)
    check("granny_lunar_birthday_stored",
          lunar_ok,
          f"birthday_lunar={lb} (expected month=7, day=7)")
else:
    check("granny_lunar_birthday_stored", False, "member not found")

# 大舅: lunar 正月十五 (month=1, day=15)
if uncle:
    lb = uncle.get("birthday_lunar") or {}
    lunar_ok = (int(lb.get("month", 0)) == 1 and int(lb.get("day", 0)) == 15)
    check("uncle_lunar_birthday_stored",
          lunar_ok,
          f"birthday_lunar={lb} (expected month=1, day=15)")
else:
    check("uncle_lunar_birthday_stored", False, "member not found")

# ── Check 4: birthday_lunar_solar_this_year computed correctly ────────────────
try:
    from lunardate import LunarDate
    today_year = date.today().year

    def expected_solar(year, month, day, is_leap=False):
        try:
            return str(LunarDate(year, month, day, is_leap).toSolarDate())
        except ValueError:
            return str(LunarDate(year, month, day, False).toSolarDate())

    if granny:
        expected = expected_solar(today_year, 7, 7)
        actual   = granny.get("birthday_lunar_solar_this_year")
        check("granny_lunar_solar_this_year",
              actual == expected,
              f"expected={expected}, actual={actual}")
    else:
        check("granny_lunar_solar_this_year", False, "member not found")

    if uncle:
        expected = expected_solar(today_year, 1, 15)
        actual   = uncle.get("birthday_lunar_solar_this_year")
        check("uncle_lunar_solar_this_year",
              actual == expected,
              f"expected={expected}, actual={actual}")
    else:
        check("uncle_lunar_solar_this_year", False, "member not found")

except ImportError:
    check("granny_lunar_solar_this_year", False, "lunardate not installed")
    check("uncle_lunar_solar_this_year",  False, "lunardate not installed")

# ── Check 5: reminders.json has an entry for 阿嬤's birthday ──────────────────
try:
    reminders = load_json(REMINDERS_PATH)
    granny_reminders = []
    if granny:
        granny_reminders = [
            r for r in reminders
            if r.get("member_id") == granny.get("id") and
               r.get("type") in ("birthday_lunar", "birthday_solar")
        ]
    reminder_exists = len(granny_reminders) > 0
    check("granny_reminder_in_json",
          reminder_exists,
          f"Found {len(granny_reminders)} reminder(s) for 阿嬤 in reminders.json")

    if reminder_exists:
        r = granny_reminders[0]
        adv = r.get("advance_days")
        check("granny_reminder_advance_days",
              adv == 3,
              f"advance_days={adv} (expected 3)")
        task_id_field = r.get("scheduled_task_id", "")
        check("granny_reminder_has_task_id",
              bool(task_id_field),
              f"scheduled_task_id={task_id_field!r}")
    else:
        check("granny_reminder_advance_days", False, "no reminder record found")
        check("granny_reminder_has_task_id",  False, "no reminder record found")

except Exception as e:
    check("granny_reminder_in_json",      False, str(e))
    check("granny_reminder_advance_days", False, str(e))
    check("granny_reminder_has_task_id",  False, str(e))

# ── Check 6: Scheduled task created for 阿嬤 birthday ────────────────────────
try:
    tasks_raw = load_json(TASKS_FILE) if os.path.exists(TASKS_FILE) else {}
    # Look for a task whose ID matches the expected pattern
    granny_task = None
    for tid, t in tasks_raw.items():
        if "阿嬤" in tid and ("birthday" in tid or "lunar" in tid or "solar" in tid):
            granny_task = t
            break
        # also accept taskId stored inside task body
        if "阿嬤" in t.get("taskId", "") and (
            "birthday" in t.get("taskId", "") or
            "lunar"    in t.get("taskId", "") or
            "solar"    in t.get("taskId", "")
        ):
            granny_task = t
            break

    check("granny_scheduled_task_created",
          granny_task is not None,
          f"Found task: {granny_task.get('taskId') if granny_task else 'None'}")

    if granny_task:
        cron = granny_task.get("cronExpression", "")
        # Validate cron format: "0 9 <day> <month> *"
        cron_parts = cron.strip().split()
        cron_valid = (
            len(cron_parts) == 5 and
            cron_parts[0] == "0" and
            cron_parts[1] == "9" and
            cron_parts[4] == "*" and
            cron_parts[2].isdigit() and
            cron_parts[3].isdigit()
        )
        check("granny_task_cron_format",
              cron_valid,
              f"cronExpression={cron!r}")

        # Validate the cron day/month: must be birthday - 3 days
        if cron_valid and granny:
            try:
                solar_str = granny.get("birthday_lunar_solar_this_year")
                if solar_str:
                    bday = date.fromisoformat(solar_str)
                    remind_date = bday - timedelta(days=3)
                    expected_cron = f"0 9 {remind_date.day} {remind_date.month} *"
                    check("granny_task_cron_correct_date",
                          cron.strip() == expected_cron,
                          f"cron={cron!r}, expected={expected_cron!r} "
                          f"(birthday={solar_str}, advance=3 days)")
                else:
                    check("granny_task_cron_correct_date", False,
                          "birthday_lunar_solar_this_year not set")
            except Exception as e2:
                check("granny_task_cron_correct_date", False, str(e2))
        else:
            check("granny_task_cron_correct_date", False,
                  "cron format invalid or member missing")
    else:
        check("granny_task_cron_format",       False, "task not found")
        check("granny_task_cron_correct_date", False, "task not found")

except Exception as e:
    check("granny_scheduled_task_created",  False, str(e))
    check("granny_task_cron_format",        False, str(e))
    check("granny_task_cron_correct_date",  False, str(e))

# ── Check 7: Annual lunar update task exists ──────────────────────────────────
try:
    tasks_raw = load_json(TASKS_FILE) if os.path.exists(TASKS_FILE) else {}
    annual_task = tasks_raw.get("member-lunar-annual-update")
    if annual_task is None:
        # also check if stored with slightly different key in the value
        for tid, t in tasks_raw.items():
            if "lunar" in tid and ("annual" in tid or "update" in tid):
                annual_task = t
                break

    check("annual_update_task_exists",
          annual_task is not None,
          f"member-lunar-annual-update task: {annual_task is not None}")

    if annual_task:
        cron = annual_task.get("cronExpression", "").strip()
        check("annual_update_task_cron",
              cron == "0 10 1 1 *",
              f"cronExpression={cron!r} (expected '0 10 1 1 *')")

        task_id_correct = annual_task.get("taskId") == "member-lunar-annual-update"
        check("annual_update_task_id",
              task_id_correct,
              f"taskId={annual_task.get('taskId')!r}")
    else:
        check("annual_update_task_cron", False, "task not found")
        check("annual_update_task_id",   False, "task not found")

except Exception as e:
    check("annual_update_task_exists", False, str(e))
    check("annual_update_task_cron",   False, str(e))
    check("annual_update_task_id",     False, str(e))

# ── Check 8: data directory permissions (700) ─────────────────────────────────
try:
    st = os.stat(BASE_DIR)
    mode = oct(st.st_mode)[-3:]
    check("data_dir_permissions_700",
          mode == "700",
          f"Permissions on {BASE_DIR}: {mode}")
except Exception as e:
    check("data_dir_permissions_700", False, str(e))

# ── Summary ───────────────────────────────────────────────────────────────────
passed_count = sum(1 for c in checks if c["passed"])
total        = len(checks)
score        = round(passed_count / total, 4)
all_passed   = passed_count == total

result = {
    "passed": all_passed,
    "score":  score,
    "checks": checks
}
print(json.dumps(result, ensure_ascii=False, indent=2))
sys.exit(0 if all_passed else 1)