#!/usr/bin/env python3
import sys
import json
import subprocess
import os
from pathlib import Path
from datetime import date, timedelta

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
skill_dir = workspace / "skills" / "lunar-reminder"
events_file = skill_dir / "data" / "events.json"
cron_log_file = workspace / "cron_operations.json"

checks = []
passed_all = True

def add_check(name, passed, detail=""):
    global passed_all
    checks.append({"name": name, "passed": passed, "detail": detail})
    if not passed:
        passed_all = False

# ── Helper: compute solar date via node ───────────────────────────────────
def lunar_to_solar(year, month, day):
    """Use the skill's own node command to get canonical solar date."""
    cmd = (
        f'const {{Lunar}}=require("lunar-javascript");'
        f'const l=Lunar.fromYmd({year},{month},{day});'
        f'const s=l.getSolar();'
        f'console.log(s.getYear()+"-"+String(s.getMonth()).padStart(2,"0")+"-"+String(s.getDay()).padStart(2,"0"));'
    )
    result = subprocess.run(
        ["node", "-e", cmd],
        capture_output=True, text=True,
        cwd=str(skill_dir)
    )
    return result.stdout.strip()  # e.g. "2026-02-11"

# ── Determine current year for cron calculation ───────────────────────────
# The agent should use the year when the task is run.
# We'll compute expected solar dates for 2026 (most likely year for these dates)
# but also accept 2025 if the agent chose a different year.
# We'll derive expected values dynamically.

CURRENT_YEAR = 2026  # canonical expected year for eval

# Expected events that must be in events.json:
expected_events = [
    {
        "name": "奶奶生日",
        "lunarMonth": 12,
        "lunarDay": 23,
        "lunarMonthName": "腊月",
        "lunarDayName": "廿三",
        "advanceDays": 2,
    },
    {
        "name": "元宵节",
        "lunarMonth": 1,
        "lunarDay": 15,
        "lunarMonthName": "正月",
        "lunarDayName": "十五",
        "advanceDays": 1,
    },
]

# Pre-existing event that must NOT be removed
PREEXISTING_NAME = "爷爷生日"

# ── Check 1: events.json exists ───────────────────────────────────────────
try:
    if not events_file.exists():
        add_check("events_json_exists", False, f"File not found: {events_file}")
        # short circuit
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        sys.exit(0)
    raw = events_file.read_text(encoding="utf-8")
    events = json.loads(raw)
    add_check("events_json_exists", True, f"Found events.json with {len(events)} entries")
except Exception as e:
    add_check("events_json_exists", False, f"Exception reading events.json: {e}")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

# ── Check 2: Pre-existing event preserved ────────────────────────────────
try:
    names = [e.get("name") for e in events]
    preserved = PREEXISTING_NAME in names
    add_check("preexisting_event_preserved", preserved,
              f"'{PREEXISTING_NAME}' {'found' if preserved else 'NOT found'} in events.json")
except Exception as e:
    add_check("preexisting_event_preserved", False, str(e))

# ── Check 3 & 4: Both new events present with correct fields ──────────────
events_by_name = {e.get("name"): e for e in events}

for exp in expected_events:
    name = exp["name"]
    try:
        if name not in events_by_name:
            add_check(f"event_present_{name}", False, f"Event '{name}' not found in events.json")
            continue
        ev = events_by_name[name]
        add_check(f"event_present_{name}", True, f"Event '{name}' found")

        # Check lunarMonth
        lm_ok = ev.get("lunarMonth") == exp["lunarMonth"]
        add_check(f"lunarMonth_{name}", lm_ok,
                  f"Expected lunarMonth={exp['lunarMonth']}, got {ev.get('lunarMonth')}")

        # Check lunarDay
        ld_ok = ev.get("lunarDay") == exp["lunarDay"]
        add_check(f"lunarDay_{name}", ld_ok,
                  f"Expected lunarDay={exp['lunarDay']}, got {ev.get('lunarDay')}")

        # Check lunarMonthName
        lmn_ok = ev.get("lunarMonthName") == exp["lunarMonthName"]
        add_check(f"lunarMonthName_{name}", lmn_ok,
                  f"Expected '{exp['lunarMonthName']}', got '{ev.get('lunarMonthName')}'")

        # Check lunarDayName
        ldn_ok = ev.get("lunarDayName") == exp["lunarDayName"]
        add_check(f"lunarDayName_{name}", ldn_ok,
                  f"Expected '{exp['lunarDayName']}', got '{ev.get('lunarDayName')}'")

        # Check advanceDays
        ad_ok = ev.get("advanceDays") == exp["advanceDays"]
        add_check(f"advanceDays_{name}", ad_ok,
                  f"Expected advanceDays={exp['advanceDays']}, got {ev.get('advanceDays')}")

        # Check reminderTime present
        rt = ev.get("reminderTime", "")
        rt_ok = bool(rt)
        add_check(f"reminderTime_present_{name}", rt_ok,
                  f"reminderTime={rt!r}")

    except Exception as e:
        add_check(f"event_check_{name}", False, str(e))

# ── Check 5: Cron log exists ──────────────────────────────────────────────
try:
    if not cron_log_file.exists():
        add_check("cron_log_exists", False, "cron_operations.json not found - sync may not have been called")
        print(json.dumps({"passed": passed_all, "score": _score(checks), "checks": checks}))
        sys.exit(0)
    cron_ops = json.loads(cron_log_file.read_text(encoding="utf-8"))
    add_check("cron_log_exists", True, f"Found {len(cron_ops)} cron operations")
except Exception as e:
    add_check("cron_log_exists", False, str(e))
    cron_ops = []

# ── Check 6: Cron operations for each new event ───────────────────────────
# Build index: name -> list of ops
cron_by_name = {}
for op in cron_ops:
    n = op.get("name", "")
    cron_by_name.setdefault(n, []).append(op)

for exp in expected_events:
    name = exp["name"]
    cron_name = f"lunar_{name}"
    try:
        ops_for = cron_by_name.get(cron_name, [])

        # Must have an "add" operation
        add_ops = [o for o in ops_for if o.get("op") == "add"]
        has_add = len(add_ops) > 0
        add_check(f"cron_add_{name}", has_add,
                  f"cron add op for '{cron_name}': {'found' if has_add else 'NOT found'}")

        if not has_add:
            continue

        add_op = add_ops[-1]  # take the last add

        # Check message format: "🔔 农历提醒：<name>将在<N>天后到来"
        expected_msg = f"🔔 农历提醒：{name}将在{exp['advanceDays']}天后到来"
        actual_msg = add_op.get("message", "")
        msg_ok = actual_msg == expected_msg
        add_check(f"cron_message_{name}", msg_ok,
                  f"Expected message: {expected_msg!r}, got: {actual_msg!r}")

        # Check timezone
        tz_ok = add_op.get("tz") == "Asia/Shanghai"
        add_check(f"cron_tz_{name}", tz_ok,
                  f"Expected tz='Asia/Shanghai', got '{add_op.get('tz')}'")

        # Check cron expression: derive expected from solar date - advanceDays
        # Try multiple years (agent might use 2025 or 2026)
        cron_expr = add_op.get("cron", "")
        cron_valid = False
        cron_detail = f"cron expr: {cron_expr!r}"
        for year in [2025, 2026, 2027]:
            try:
                solar_str = lunar_to_solar(year, exp["lunarMonth"], exp["lunarDay"])
                if not solar_str:
                    continue
                solar_date = date.fromisoformat(solar_str)
                reminder_date = solar_date - timedelta(days=exp["advanceDays"])
                # Get reminderTime from the event if possible
                ev = events_by_name.get(name, {})
                rt = ev.get("reminderTime", "09:00")
                try:
                    h, m = rt.split(":")
                    hour, minute = int(h), int(m)
                except Exception:
                    hour, minute = 9, 0

                expected_cron = f"{minute} {hour} {reminder_date.day} {reminder_date.month} *"
                if cron_expr.strip() == expected_cron.strip():
                    cron_valid = True
                    cron_detail = f"Matched cron for year {year}: {expected_cron}"
                    break
            except Exception as ce:
                cron_detail += f" (year {year} error: {ce})"

        add_check(f"cron_expr_{name}", cron_valid, cron_detail)

    except Exception as e:
        add_check(f"cron_check_{name}", False, str(e))

# ── Check 7: rm op before add ─────────────────────────────────────────────
for exp in expected_events:
    name = exp["name"]
    cron_name = f"lunar_{name}"
    try:
        ops_for = cron_by_name.get(cron_name, [])
        rm_ops = [o for o in ops_for if o.get("op") == "rm"]
        add_ops = [o for o in ops_for if o.get("op") == "add"]
        # rm should appear before add in the log
        all_ops_ordered = [(i, o) for i, o in enumerate(cron_ops)
                           if o.get("name") == cron_name]
        rm_indices = [i for i, o in all_ops_ordered if o.get("op") == "rm"]
        add_indices = [i for i, o in all_ops_ordered if o.get("op") == "add"]
        if rm_indices and add_indices:
            order_ok = min(rm_indices) < max(add_indices)
        else:
            order_ok = False
        add_check(f"cron_rm_before_add_{name}", order_ok,
                  f"rm_indices={rm_indices}, add_indices={add_indices}")
    except Exception as e:
        add_check(f"cron_rm_before_add_{name}", False, str(e))

# ── Score ─────────────────────────────────────────────────────────────────
def _score(checks):
    if not checks:
        return 0.0
    # Weight critical checks more
    critical = ["events_json_exists", "preexisting_event_preserved"]
    total = len(checks)
    passed = sum(1 for c in checks if c["passed"])
    return round(passed / total, 3)

final_score = _score(checks)
result = {
    "passed": all(c["passed"] for c in checks),
    "score": final_score,
    "checks": checks
}
print(json.dumps(result, ensure_ascii=False, indent=2))