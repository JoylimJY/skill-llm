import json
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

def run_check(name, fn):
    try:
        passed, detail = fn()
        return {"name": name, "passed": passed, "detail": detail}
    except Exception as e:
        return {"name": name, "passed": False, "detail": f"Exception: {e}"}

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []
    
    # Find habit-cli.js
    cli_candidates = list(Path(workspace).rglob("habit-cli.js"))
    if not cli_candidates:
        cli_candidates = [Path("/workspace/habit-tracker/scripts/habit-cli.js")]
    cli_path = str(cli_candidates[0]) if cli_candidates else "/workspace/habit-tracker/scripts/habit-cli.js"
    
    def run_cli(args):
        result = subprocess.run(
            ["node", cli_path] + args,
            capture_output=True, text=True, timeout=30
        )
        return result.stdout + result.stderr

    # --- Check 1: habits.json exists with all 3 habits ---
    def check_habits_created():
        config_dir = Path.home() / ".config" / "habit-tracker"
        habits_file = config_dir / "habits.json"
        if not habits_file.exists():
            return False, f"habits.json not found at {habits_file}"
        data = json.loads(habits_file.read_text())
        # Could be array or object with habits key
        if isinstance(data, list):
            habits = data
        elif isinstance(data, dict):
            habits = data.get("habits", data.get("items", []))
        else:
            return False, f"Unexpected habits.json format: {type(data)}"
        
        names = [h.get("name", h.get("habit", "")).lower() for h in habits]
        has_walk = any("walk" in n or "morning walk" in n.lower() for n in names)
        has_reading = any("read" in n for n in names)
        has_review = any("review" in n or "weekly" in n for n in names)
        
        if not (has_walk and has_reading and has_review):
            return False, f"Expected 3 habits (Morning Walk, Reading, Weekly Review). Found names: {names}"
        return True, f"All 3 habits found: {names}"
    
    checks.append(run_check("Three habits created in habits.json", check_habits_created))

    # --- Check 2: Morning Walk configured as daily, target 1, reminder 07:00 ---
    def check_morning_walk_config():
        config_dir = Path.home() / ".config" / "habit-tracker"
        habits_file = config_dir / "habits.json"
        if not habits_file.exists():
            return False, "habits.json not found"
        data = json.loads(habits_file.read_text())
        habits = data if isinstance(data, list) else data.get("habits", [])
        
        walk = None
        for h in habits:
            n = h.get("name", "").lower()
            if "walk" in n or "morning walk" in n:
                walk = h
                break
        if not walk:
            return False, "Morning Walk habit not found"
        
        freq = walk.get("frequency", walk.get("freq", "")).lower()
        target = int(walk.get("target", walk.get("goal", 0)))
        reminder = walk.get("reminder", walk.get("reminderTime", ""))
        
        issues = []
        if freq != "daily":
            issues.append(f"frequency={freq} (expected daily)")
        if target != 1:
            issues.append(f"target={target} (expected 1)")
        if "07:00" not in str(reminder) and "7:00" not in str(reminder):
            issues.append(f"reminder={reminder} (expected 07:00)")
        
        if issues:
            return False, f"Morning Walk config issues: {'; '.join(issues)}"
        return True, f"Morning Walk correctly configured: freq={freq}, target={target}, reminder={reminder}"
    
    checks.append(run_check("Morning Walk: daily, target=1, reminder=07:00", check_morning_walk_config))

    # --- Check 3: Weekly Review configured as weekly ---
    def check_weekly_review_config():
        config_dir = Path.home() / ".config" / "habit-tracker"
        habits_file = config_dir / "habits.json"
        if not habits_file.exists():
            return False, "habits.json not found"
        data = json.loads(habits_file.read_text())
        habits = data if isinstance(data, list) else data.get("habits", [])
        
        review = None
        for h in habits:
            n = h.get("name", "").lower()
            if "review" in n or ("weekly" in n):
                review = h
                break
        if not review:
            return False, "Weekly Review habit not found"
        
        freq = review.get("frequency", review.get("freq", "")).lower()
        if freq != "weekly":
            return False, f"Weekly Review frequency={freq} (expected weekly)"
        return True, f"Weekly Review correctly configured as weekly"
    
    checks.append(run_check("Weekly Review: configured as weekly frequency", check_weekly_review_config))

    # --- Check 4: logs.json has backdated entries for Morning Walk ---
    def check_backdated_walk_logs():
        config_dir = Path.home() / ".config" / "habit-tracker"
        logs_file = config_dir / "logs.json"
        if not logs_file.exists():
            return False, f"logs.json not found at {logs_file}"
        data = json.loads(logs_file.read_text())
        logs = data if isinstance(data, list) else data.get("logs", [])
        
        # Find walk logs
        walk_logs = [l for l in logs if "walk" in l.get("habit", l.get("name", "")).lower()]
        
        if len(walk_logs) < 15:
            return False, f"Expected at least 15 Morning Walk log entries (22 in self-reported), found {len(walk_logs)}"
        
        # Check that logs span multiple different dates (backdating worked)
        dates = set()
        for l in walk_logs:
            d = l.get("date", l.get("timestamp", l.get("completedAt", "")))
            if d:
                dates.add(str(d)[:10])
        
        if len(dates) < 15:
            return False, f"Expected logs on at least 15 distinct dates, found {len(dates)} dates: {sorted(dates)[:5]}..."
        
        # Check that oldest date is at least 20 days before today-ish (around 2024-03-18)
        oldest = min(dates)
        if oldest > "2024-03-25":
            return False, f"Oldest Morning Walk log date is {oldest}, expected entries going back to ~2024-03-19 (backdated)"
        
        return True, f"Morning Walk has {len(walk_logs)} logs across {len(dates)} distinct dates, oldest: {oldest}"
    
    checks.append(run_check("Morning Walk: backdated log entries span 28-day period", check_backdated_walk_logs))

    # --- Check 5: logs.json has backdated entries for Reading ---
    def check_backdated_reading_logs():
        config_dir = Path.home() / ".config" / "habit-tracker"
        logs_file = config_dir / "logs.json"
        if not logs_file.exists():
            return False, "logs.json not found"
        data = json.loads(logs_file.read_text())
        logs = data if isinstance(data, list) else data.get("logs", [])
        
        reading_logs = [l for l in logs if "read" in l.get("habit", l.get("name", "")).lower()]
        
        if len(reading_logs) < 12:
            return False, f"Expected at least 12 Reading log entries (18 in self-reported), found {len(reading_logs)}"
        
        dates = set()
        for l in reading_logs:
            d = l.get("date", l.get("timestamp", l.get("completedAt", "")))
            if d:
                dates.add(str(d)[:10])
        
        if len(dates) < 12:
            return False, f"Expected logs on at least 12 distinct dates, found {len(dates)}"
        
        return True, f"Reading has {len(reading_logs)} logs across {len(dates)} distinct dates"
    
    checks.append(run_check("Reading: backdated log entries span 28-day period", check_backdated_reading_logs))

    # --- Check 6: Weekly Review has log entries ---
    def check_weekly_review_logs():
        config_dir = Path.home() / ".config" / "habit-tracker"
        logs_file = config_dir / "logs.json"
        if not logs_file.exists():
            return False, "logs.json not found"
        data = json.loads(logs_file.read_text())
        logs = data if isinstance(data, list) else data.get("logs", [])
        
        review_logs = [l for l in logs if "review" in l.get("habit", l.get("name", "")).lower() 
                       or ("weekly" in l.get("habit", l.get("name", "")).lower())]
        
        if len(review_logs) < 2:
            return False, f"Expected at least 2 Weekly Review log entries (3 in self-reported: weeks 1,2,4), found {len(review_logs)}"
        
        return True, f"Weekly Review has {len(review_logs)} log entries"
    
    checks.append(run_check("Weekly Review: log entries present for completed weeks", check_weekly_review_logs))

    # --- Check 7: stats report file created ---
    def check_stats_report_file():
        # Look for the progress_report.json or stats_report.json file
        report_candidates = list(Path(workspace).rglob("progress_report.json"))
        if not report_candidates:
            report_candidates = list(Path(workspace).rglob("wellness_report.json"))
        if not report_candidates:
            report_candidates = list(Path(workspace).rglob("stats_report.json"))
        if not report_candidates:
            # Check home dir too
            report_candidates = list(Path.home().rglob("progress_report.json"))
        
        if not report_candidates:
            return False, "No progress_report.json (or wellness_report.json / stats_report.json) found anywhere in workspace"
        
        report_path = report_candidates[0]
        content = report_path.read_text()
        
        try:
            report_data = json.loads(content)
        except json.JSONDecodeError:
            return False, f"Found report at {report_path} but it is not valid JSON"
        
        # Check it has some meaningful content
        content_str = json.dumps(report_data).lower()
        has_walk = "walk" in content_str or "morning" in content_str
        has_reading = "read" in content_str
        has_review = "review" in content_str or "weekly" in content_str
        
        if not (has_walk and has_reading):
            return False, f"Report at {report_path} doesn't mention expected habits. Keys: {list(report_data.keys()) if isinstance(report_data, dict) else 'list'}"
        
        return True, f"Progress report found at {report_path} with habit data for all tracked habits"
    
    checks.append(run_check("progress_report.json created with all habit stats", check_stats_report_file))

    # --- Check 8: Stats show correct completion rate for Morning Walk ---
    def check_walk_completion_rate():
        # Run stats command and parse output
        try:
            output = run_cli(["stats", "Morning Walk", "--days", "28"])
        except Exception as e:
            return False, f"Could not run stats command: {e}"
        
        # Expected: 22/28 days = ~78.6% completion rate
        # Also check streak calculation
        if not output or len(output.strip()) < 10:
            return False, f"stats command returned empty output: '{output}'"
        
        # Look for completion rate in output (should be around 78-79%)
        import re
        rate_match = re.search(r'(\d+(?:\.\d+)?)\s*%', output)
        if rate_match:
            rate = float(rate_match.group(1))
            if 70 <= rate <= 85:
                return True, f"Morning Walk completion rate is {rate}% (expected ~78.6% for 22/28 days)"
            else:
                return False, f"Morning Walk completion rate is {rate}%, expected ~78.6% (22/28 days logged)"
        
        # If no percentage found, check for raw count
        count_match = re.search(r'(\d+)\s*(?:completions?|times?|total)', output.lower())
        if count_match:
            count = int(count_match.group(1))
            if count >= 18:
                return True, f"Morning Walk shows {count} completions in stats output (backdating worked)"
            else:
                return False, f"Morning Walk shows only {count} completions (expected ~22)"
        
        # Fallback: at least verify logs exist and output isn't an error
        if "error" in output.lower() or "not found" in output.lower():
            return False, f"Stats command error: {output[:200]}"
        
        return True, f"Stats command ran successfully: {output[:150]}"
    
    checks.append(run_check("Morning Walk stats show ~78% completion rate over 28 days", check_walk_completion_rate))

    # --- Check 9: Reading reminder set to 21:30 ---
    def check_reading_reminder():
        config_dir = Path.home() / ".config" / "habit-tracker"
        habits_file = config_dir / "habits.json"
        if not habits_file.exists():
            return False, "habits.json not found"
        data = json.loads(habits_file.read_text())
        habits = data if isinstance(data, list) else data.get("habits", [])
        
        reading = None
        for h in habits:
            n = h.get("name", "").lower()
            if "read" in n:
                reading = h
                break
        if not reading:
            return False, "Reading habit not found"
        
        reminder = str(reading.get("reminder", reading.get("reminderTime", "")))
        if "21:30" in reminder or "21:30" in reminder:
            return True, f"Reading reminder correctly set to 21:30"
        else:
            return False, f"Reading reminder is '{reminder}', expected 21:30"
    
    checks.append(run_check("Reading habit: reminder set to 21:30", check_reading_reminder))

    # --- Check 10: Total log count is reasonable (at least 40 entries total) ---
    def check_total_log_volume():
        config_dir = Path.home() / ".config" / "habit-tracker"
        logs_file = config_dir / "logs.json"
        if not logs_file.exists():
            return False, "logs.json not found"
        data = json.loads(logs_file.read_text())
        logs = data if isinstance(data, list) else data.get("logs", [])
        
        total = len(logs)
        # Expected: 22 walk + 18 reading + 3 weekly = 43 total
        if total < 35:
            return False, f"Total log entries: {total}, expected at least 35 (22 walk + 18 reading + 3 weekly review)"
        return True, f"Total log entries: {total} (expected ~43)"
    
    checks.append(run_check("Total log volume: at least 35 backdated entries", check_total_log_volume))

    # --- Scoring ---
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)
    overall_passed = passed_count >= 7  # Must pass at least 7/10 checks

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()