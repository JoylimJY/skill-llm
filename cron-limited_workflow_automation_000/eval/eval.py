#!/usr/bin/env python3
import sys
import json
import os
import subprocess
from pathlib import Path
from datetime import date, timedelta

try:
    from lunarcalendar import Converter, Lunar
    import pytz
except ImportError:
    print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "dependencies", "passed": False, "detail": "lunarcalendar or pytz not installed"}]}))
    sys.exit(0)

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
home = Path(os.path.expanduser("~"))
call_log_path = home / ".openclaw" / "call_log.jsonl"
birthdays_json_path = home / ".openclaw" / "cron-limited" / "birthdays.json"

checks = []

def load_call_log():
    entries = []
    if not call_log_path.exists():
        return entries
    try:
        with open(call_log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
    except Exception as e:
        pass
    return entries

def args_to_dict(args):
    """Parse a list of CLI args into a dict of flag->value."""
    d = {}
    i = 0
    while i < len(args):
        if args[i].startswith("--"):
            key = args[i]
            if i + 1 < len(args) and not args[i+1].startswith("--"):
                d[key] = args[i+1]
                i += 2
            else:
                d[key] = True
                i += 1
        else:
            i += 1
    return d

all_calls = load_call_log()

# ─────────────────────────────────────────────────
# CHECK 1: cron-limited add (water reminder, 4m, 5 times)
# ─────────────────────────────────────────────────
check1_passed = False
check1_detail = "No matching 'cron-limited add' call found"

for entry in all_calls:
    args = entry.get("args", [])
    if len(args) >= 2 and args[0] == "cron-limited" and args[1] == "add":
        d = args_to_dict(args[2:])
        every_ok = d.get("--every", "").strip() == "4m"
        repeat_ok = str(d.get("--repeat", "")).strip() == "5"
        message_ok = "喝水" in d.get("--message", "") or "💧" in d.get("--message", "")
        channel_ok = d.get("--channel", "").strip() == "openclaw-weixin"
        to_ok = d.get("--to", "").strip() == "user-abc123@im.wechat"
        if every_ok and repeat_ok and message_ok and channel_ok and to_ok:
            check1_passed = True
            check1_detail = f"Found correct call: every=4m, repeat=5, message contains 喝水/💧, channel=openclaw-weixin, to=user-abc123@im.wechat"
            break
        else:
            check1_detail = (
                f"Found 'cron-limited add' but wrong params: "
                f"every={d.get('--every')!r} (need 4m), "
                f"repeat={d.get('--repeat')!r} (need 5), "
                f"message_ok={message_ok}, channel_ok={channel_ok}, to_ok={to_ok}"
            )

checks.append({"name": "limited_repeat_water_reminder", "passed": check1_passed, "detail": check1_detail})

# ─────────────────────────────────────────────────
# CHECK 2: cron-limited add-lunar (Bob birthday, lunar 7-20, 2 days before, yearly, 09:30)
# ─────────────────────────────────────────────────
check2_passed = False
check2_detail = "No matching 'cron-limited add-lunar' call found"

for entry in all_calls:
    args = entry.get("args", [])
    if len(args) >= 2 and args[0] == "cron-limited" and args[1] == "add-lunar":
        d = args_to_dict(args[2:])
        lunar_ok = d.get("--lunar", "").strip() == "7-20"
        days_before_ok = str(d.get("--days-before", "")).strip() == "2"
        yearly_ok = "--yearly" in args or d.get("--yearly") is True
        time_ok = d.get("--time", "").strip() == "09:30"
        message_ok = "Bob" in d.get("--message", "") or "生日" in d.get("--message", "")
        channel_ok = d.get("--channel", "").strip() == "openclaw-weixin"
        to_ok = d.get("--to", "").strip() == "manager-xyz@im.wechat"
        if lunar_ok and days_before_ok and yearly_ok and time_ok and channel_ok and to_ok:
            check2_passed = True
            check2_detail = (
                f"Found correct call: lunar=7-20, days-before=2, yearly=True, "
                f"time=09:30, channel=openclaw-weixin, to=manager-xyz@im.wechat"
            )
            break
        else:
            check2_detail = (
                f"Found 'add-lunar' but wrong params: "
                f"lunar={d.get('--lunar')!r}(need 7-20), "
                f"days-before={d.get('--days-before')!r}(need 2), "
                f"yearly={yearly_ok}, time={d.get('--time')!r}(need 09:30), "
                f"channel_ok={channel_ok}, to_ok={to_ok}"
            )

checks.append({"name": "lunar_birthday_add_lunar", "passed": check2_passed, "detail": check2_detail})

# ─────────────────────────────────────────────────
# CHECK 3: birthdays.json exists and has correct structure
# ─────────────────────────────────────────────────
check3_passed = False
check3_detail = "birthdays.json not found at ~/.openclaw/cron-limited/birthdays.json"

try:
    if birthdays_json_path.exists():
        with open(birthdays_json_path, "r", encoding="utf-8") as f:
            bdays = json.load(f)
        if isinstance(bdays, list) and len(bdays) >= 1:
            # Find entry for lunar 7-20
            bob_entry = None
            for b in bdays:
                if b.get("lunar_month") == 7 and b.get("lunar_day") == 20:
                    bob_entry = b
                    break
            if bob_entry:
                has_message = bool(bob_entry.get("message"))
                has_days_before = bob_entry.get("days_before") == 2
                has_time = bob_entry.get("time") == "09:30"
                has_channel = bob_entry.get("channel") == "openclaw-weixin"
                has_to = bob_entry.get("to") == "manager-xyz@im.wechat"
                if has_message and has_days_before and has_time and has_channel and has_to:
                    check3_passed = True
                    check3_detail = "birthdays.json has correct entry for lunar 7-20 Bob birthday"
                else:
                    check3_detail = (
                        f"birthdays.json entry found but incorrect: "
                        f"days_before={bob_entry.get('days_before')!r}(need 2), "
                        f"time={bob_entry.get('time')!r}(need 09:30), "
                        f"channel={bob_entry.get('channel')!r}, to={bob_entry.get('to')!r}"
                    )
            else:
                check3_detail = f"No entry with lunar_month=7, lunar_day=20 found in birthdays.json. Entries: {[{'m':b.get('lunar_month'),'d':b.get('lunar_day')} for b in bdays]}"
        else:
            check3_detail = f"birthdays.json is not a non-empty list: {type(bdays)}"
    else:
        check3_detail = f"File does not exist: {birthdays_json_path}"
except Exception as e:
    check3_detail = f"Error reading birthdays.json: {e}"

checks.append({"name": "birthdays_json_structure", "passed": check3_passed, "detail": check3_detail})

# ─────────────────────────────────────────────────
# CHECK 4: daily_check_sim.py exists and calls openclaw agent with correct message format
# ─────────────────────────────────────────────────
check4_passed = False
check4_detail = "daily_check_sim.py not found in workspace"

sim_files = list(workspace.rglob("daily_check_sim.py"))

if sim_files:
    sim_path = sim_files[0]
    # Compute expected solar date for lunar 7-20, 2025
    try:
        solar_obj = Converter.Lunar2Solar(Lunar(2025, 7, 20, False))
        solar_date = date(solar_obj.year, solar_obj.month, solar_obj.day)
        reminder_date = solar_date - timedelta(days=2)
        expected_solar_str = solar_date.strftime("%Y-%m-%d")
        # Run the script and check if the openclaw agent call has correct message
        # We temporarily set today's date context via env and run the script
        # The script should invoke openclaw with the advance-reminder message format
        # Expected message: f"📅 提醒：农历7月20日是 {solar_date_str}，还有 2 天！\n{custom_message}"
        
        # Run the script (it should call openclaw agent which logs to call_log.jsonl)
        log_before = load_call_log()
        log_before_count = len(log_before)
        
        env = os.environ.copy()
        env["CRON_LIMITED_DAILY_CHECK"] = "1"
        # We inject today as the reminder date so the script runs correctly
        env["MOCK_TODAY"] = reminder_date.isoformat()
        
        result = subprocess.run(
            ["python3", str(sim_path)],
            capture_output=True,
            text=True,
            timeout=30,
            env=env
        )
        
        log_after = load_call_log()
        new_calls = log_after[log_before_count:]
        
        agent_call_found = False
        correct_format = False
        found_detail = f"Script ran (rc={result.returncode}). New calls: {len(new_calls)}. stdout: {result.stdout[:300]!r}. stderr: {result.stderr[:300]!r}"
        
        for entry in new_calls:
            args = entry.get("args", [])
            if "agent" in args:
                agent_call_found = True
                # Check message format: must contain the advance reminder format
                d = args_to_dict(args)
                msg = d.get("--message", "")
                # Required format: 📅 提醒：农历7月20日是 {solar_date}，还有 2 天！
                has_emoji = "📅" in msg
                has_lunar_ref = "农历" in msg and "7" in msg and "20" in msg
                has_days_remaining = "还有" in msg and "2" in msg and "天" in msg
                has_solar_date = solar_date.strftime("%Y-%m-%d") in msg or f"{solar_date.month}月{solar_date.day}日" in msg or expected_solar_str in msg
                has_deliver = "--deliver" in args
                has_channel = d.get("--channel", "") == "openclaw-weixin"
                has_to = d.get("--to", "") == "manager-xyz@im.wechat"
                
                if has_emoji and has_lunar_ref and has_days_remaining and has_deliver and has_channel and has_to:
                    correct_format = True
                    found_detail = (
                        f"Correct agent call: message contains 📅 advance reminder format, "
                        f"has --deliver, channel=openclaw-weixin, to=manager-xyz@im.wechat. "
                        f"Message: {msg[:200]!r}"
                    )
                    break
                else:
                    found_detail = (
                        f"Agent call found but format issues: "
                        f"has_📅={has_emoji}, has_lunar_ref={has_lunar_ref}, "
                        f"has_days_remaining={has_days_remaining}, has_solar_date={has_solar_date}, "
                        f"has_deliver={has_deliver}, channel_ok={has_channel}, to_ok={has_to}. "
                        f"Message: {msg[:200]!r}"
                    )
        
        if not agent_call_found:
            found_detail = f"Script ran but no 'openclaw agent' call found in new log entries. {found_detail}"
        
        check4_passed = correct_format
        check4_detail = found_detail
        
    except Exception as e:
        check4_detail = f"Error computing expected date or running script: {e}"
else:
    check4_detail = "daily_check_sim.py not found anywhere in workspace"

checks.append({"name": "daily_check_sim_correct_format", "passed": check4_passed, "detail": check4_detail})

# ─────────────────────────────────────────────────
# CHECK 5: daily check cron setup (every day 7am cron for the daily check)
# This checks that the agent called 'openclaw cron-limited add' or similar for daily check
# OR that there's evidence of a daily cron being set up
# ─────────────────────────────────────────────────
check5_passed = False
check5_detail = "No evidence of daily check cron task setup"

for entry in all_calls:
    args = entry.get("args", [])
    args_str = " ".join(str(a) for a in args)
    # Look for evidence of daily check setup - cron task for CRON-LIMITED-DAILY-CHECK
    if "CRON-LIMITED-DAILY-CHECK" in args_str or "daily" in args_str.lower():
        check5_passed = True
        check5_detail = f"Found daily check cron setup call: {args_str[:200]}"
        break
    # Also check crontab
    if "crontab" in args_str.lower():
        check5_passed = True
        check5_detail = f"Found crontab-related call: {args_str[:200]}"
        break

# Also check if crontab was set up via shell
try:
    crontab_result = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=5)
    if "CRON-LIMITED-DAILY-CHECK" in crontab_result.stdout or "cron-limited" in crontab_result.stdout:
        check5_passed = True
        check5_detail = f"Crontab contains daily check: {crontab_result.stdout[:300]}"
except Exception as e:
    pass

# Relax: if birthdays.json exists and is correct, the infrastructure implies daily check would work
# Check if daily check task was discussed in any file
for f in workspace.rglob("*.sh"):
    try:
        content = f.read_text(encoding="utf-8", errors="ignore")
        if "CRON-LIMITED-DAILY-CHECK" in content:
            check5_passed = True
            check5_detail = f"Found CRON-LIMITED-DAILY-CHECK in {f}"
            break
    except:
        pass

for f in workspace.rglob("*.py"):
    try:
        content = f.read_text(encoding="utf-8", errors="ignore")
        if "CRON-LIMITED-DAILY-CHECK" in content:
            check5_passed = True
            check5_detail = f"Found CRON-LIMITED-DAILY-CHECK reference in {f}"
            break
    except:
        pass

checks.append({"name": "daily_check_cron_setup", "passed": check5_passed, "detail": check5_detail})

# ─────────────────────────────────────────────────
# SCORING
# ─────────────────────────────────────────────────
weights = {
    "limited_repeat_water_reminder": 0.25,
    "lunar_birthday_add_lunar": 0.25,
    "birthdays_json_structure": 0.20,
    "daily_check_sim_correct_format": 0.25,
    "daily_check_cron_setup": 0.05,
}

score = sum(weights[c["name"]] for c in checks if c["passed"])
passed = score >= 0.7

result = {
    "passed": passed,
    "score": round(score, 4),
    "checks": checks
}

print(json.dumps(result, ensure_ascii=False, indent=2))