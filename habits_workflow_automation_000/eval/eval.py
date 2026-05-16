#!/usr/bin/env python3
"""
Evaluation script for the habit tracking task.
Usage: python eval_script.py <workspace_dir>
"""
import sys
import json
import re
from pathlib import Path
from datetime import date, timedelta

def find_habit_file(habits_dir: Path, name: str):
    """Find a habit file by name (case-insensitive, partial match)."""
    candidates = list(habits_dir.glob(f"*{name}*"))
    return candidates[0] if candidates else None

def parse_log_entries(content: str):
    """Extract date->done mappings from a habit markdown file."""
    entries = {}
    # Match lines like: | 2024-03-15 | yes | ... or similar table/list formats
    # Accept both table (| date | yes/no |) and simple (date: yes/no) formats
    date_pattern = re.compile(
        r'(\d{4}-\d{2}-\d{2})[^\n]*\b(yes|no)\b',
        re.IGNORECASE
    )
    for m in date_pattern.finditer(content):
        d = m.group(1)
        done = m.group(2).lower() == 'yes'
        entries[d] = done
    return entries

def check_file_exists(habits_dir: Path, name: str, label: str):
    f = find_habit_file(habits_dir, name)
    if f is None:
        return False, f"{label} file not found in {habits_dir}"
    return True, str(f)

def check_log_entries(habits_dir: Path, name: str, expected_dates: list):
    """Verify that the habit file contains log entries for expected dates."""
    f = find_habit_file(habits_dir, name)
    if f is None:
        return False, f"File for {name} not found"
    content = f.read_text()
    entries = parse_log_entries(content)
    found = [d for d in expected_dates if d in entries]
    missing = [d for d in expected_dates if d not in entries]
    if len(found) >= len(expected_dates) * 0.8:  # 80% threshold
        return True, f"Found {len(found)}/{len(expected_dates)} expected dates"
    return False, f"Missing dates: {missing[:5]}"

def check_streak_present(habits_dir: Path, name: str):
    """Check that the habit file mentions both current streak and best streak."""
    f = find_habit_file(habits_dir, name)
    if f is None:
        return False, f"File for {name} not found"
    content = f.read_text().lower()
    has_current = bool(re.search(r'current.{0,20}streak|streak.{0,20}current', content))
    has_best = bool(re.search(r'best.{0,20}streak|streak.{0,20}best|all.?time', content))
    if has_current and has_best:
        return True, "Both current and best streak found"
    missing = []
    if not has_current:
        missing.append("current streak")
    if not has_best:
        missing.append("best streak")
    return False, f"Missing: {', '.join(missing)}"

def check_frequency_in_file(habits_dir: Path, name: str, freq_keyword: str):
    """Check that the habit file mentions its frequency type."""
    f = find_habit_file(habits_dir, name)
    if f is None:
        return False, f"File for {name} not found"
    content = f.read_text().lower()
    if freq_keyword.lower() in content:
        return True, f"Frequency '{freq_keyword}' found in {name} file"
    return False, f"Frequency '{freq_keyword}' not found in {name} file"

def compute_expected_streaks_client_calls():
    """
    client_calls: weekdays only (Mon-Fri). Weekends are ignored.
    Log (weekdays only, ascending):
      2024-03-01 Fri  YES
      2024-03-04 Mon  NO   <- miss
      2024-03-05 Tue  YES
      2024-03-06 Wed  YES
      2024-03-07 Thu  YES
      2024-03-08 Fri  YES
      2024-03-11 Mon  YES
      2024-03-12 Tue  YES
      2024-03-13 Wed  NO   <- miss
      2024-03-14 Thu  YES
      2024-03-15 Fri  YES
    
    Current streak (from most recent, going back): Mar15=YES, Mar14=YES, Mar13=NO -> current=2
    Best streak: Mar5-Mar12 = YES,YES,YES,YES,YES,YES = 6 consecutive weekdays
    """
    current = 2
    best = 6
    return current, best

def compute_expected_streaks_journaling():
    """
    journaling: daily.
    Log (ascending):
      2024-03-01 NO
      2024-03-02 YES
      2024-03-03 YES
      2024-03-04 YES
      2024-03-05 YES
      2024-03-06 YES
      2024-03-07 YES
      2024-03-08 YES
      2024-03-09 YES
      2024-03-10 NO
      2024-03-11 YES
      2024-03-12 NO
      2024-03-13 YES
      2024-03-14 YES
      2024-03-15 YES
    
    Current streak (from Mar15 backward): Mar15=YES,Mar14=YES,Mar13=YES,Mar12=NO -> current=3
    Best streak: Mar2-Mar9 = 8 consecutive days
    """
    current = 3
    best = 8
    return current, best

def check_streak_values(habits_dir: Path, name: str, expected_current: int, expected_best: int):
    """Check that streak numbers appear in the file (within ±1 tolerance for edge cases)."""
    f = find_habit_file(habits_dir, name)
    if f is None:
        return False, f"File for {name} not found"
    content = f.read_text()
    numbers = [int(x) for x in re.findall(r'\b\d+\b', content)]
    
    current_ok = expected_current in numbers or (expected_current - 1) in numbers
    best_ok = expected_best in numbers or (expected_best - 1) in numbers
    
    detail = f"Numbers found: {sorted(set(numbers))}; expected current={expected_current}, best={expected_best}"
    return (current_ok and best_ok), detail

def check_exercise_weekly_logic(habits_dir: Path):
    """
    exercise: 3x/week. Flexible days.
    Week of Mar 4-10: Mon=NO, Tue=YES, Wed=YES, Thu=YES, Fri=NO, Sat=NO, Sun=YES = 4 days >= 3 ✓
    Week of Mar 11-17: Mon=NO, Tue=YES, Wed=NO, Thu=YES, Fri=NO = 2 days < 3 ✗ (partial week)
    
    Check that the file acknowledges weekly frequency / 3x per week logic.
    """
    f = find_habit_file(habits_dir, "exercise")
    if f is None:
        return False, "exercise file not found"
    content = f.read_text().lower()
    has_weekly = bool(re.search(r'3.{0,10}(week|per week|times)|weekly|x.{0,5}week', content))
    if has_weekly:
        return True, "Weekly/3x-per-week frequency logic found in exercise file"
    return False, "No mention of 3x/week or weekly frequency in exercise file"

def check_summary_file(habits_dir: Path):
    """
    summary.md must exist and contain:
    1. Completion rate per habit
    2. Day-of-week analysis (strongest/weakest days)
    3. Streak status for all habits
    """
    summary_path = habits_dir / "summary.md"
    if not summary_path.exists():
        # Try to find it
        candidates = list(habits_dir.glob("summary*"))
        if not candidates:
            return False, "summary.md not found in habits/"
        summary_path = candidates[0]
    
    content = summary_path.read_text().lower()
    
    checks = {
        "completion_rate": bool(re.search(r'completion|rate|percent|%|\d+/\d+', content)),
        "day_analysis": bool(re.search(r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun).{0,50}(strong|weak|best|worst|miss|never|always)', content)),
        "streak_status": bool(re.search(r'streak', content)),
        "all_three_habits": all(h in content for h in ['client_calls', 'journaling', 'exercise']),
    }
    
    passed = sum(checks.values())
    detail = "; ".join(f"{k}={'✓' if v else '✗'}" for k, v in checks.items())
    return passed >= 3, f"Summary checks ({passed}/4 passed): {detail}"

def check_habits_dir_structure(workspace: Path):
    """~/habits/ must exist with at least 3 habit files + summary.md"""
    habits_dir = workspace / "habits"
    if not habits_dir.exists():
        return False, habits_dir, "habits/ directory does not exist"
    
    md_files = list(habits_dir.glob("*.md"))
    if len(md_files) < 4:
        return False, habits_dir, f"Expected at least 4 .md files (3 habits + summary), found {len(md_files)}: {[f.name for f in md_files]}"
    return True, habits_dir, f"habits/ exists with {len(md_files)} .md files: {[f.name for f in md_files]}"

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/root")
    
    checks = []
    total_score = 0.0
    
    # ── Check 1: habits/ directory structure ─────────────────────────────────
    dir_ok, habits_dir, dir_detail = check_habits_dir_structure(workspace)
    checks.append({"name": "habits_directory_structure", "passed": dir_ok, "detail": dir_detail})
    if dir_ok:
        total_score += 0.10
    
    if not dir_ok:
        # Can't continue without the directory
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result))
        return

    # ── Check 2: client_calls.md exists ──────────────────────────────────────
    try:
        ok, detail = check_file_exists(habits_dir, "client_call", "client_calls")
        checks.append({"name": "client_calls_file_exists", "passed": ok, "detail": detail})
        if ok: total_score += 0.05
    except Exception as e:
        checks.append({"name": "client_calls_file_exists", "passed": False, "detail": str(e)})

    # ── Check 3: journaling.md exists ────────────────────────────────────────
    try:
        ok, detail = check_file_exists(habits_dir, "journal", "journaling")
        checks.append({"name": "journaling_file_exists", "passed": ok, "detail": detail})
        if ok: total_score += 0.05
    except Exception as e:
        checks.append({"name": "journaling_file_exists", "passed": False, "detail": str(e)})

    # ── Check 4: exercise.md exists ──────────────────────────────────────────
    try:
        ok, detail = check_file_exists(habits_dir, "exercise", "exercise")
        checks.append({"name": "exercise_file_exists", "passed": ok, "detail": detail})
        if ok: total_score += 0.05
    except Exception as e:
        checks.append({"name": "exercise_file_exists", "passed": False, "detail": str(e)})

    # ── Check 5: client_calls log entries present ────────────────────────────
    try:
        expected_dates = [f"2024-03-{str(d).zfill(2)}" for d in range(1, 16)]
        ok, detail = check_log_entries(habits_dir, "client_call", expected_dates)
        checks.append({"name": "client_calls_log_entries", "passed": ok, "detail": detail})
        if ok: total_score += 0.08
    except Exception as e:
        checks.append({"name": "client_calls_log_entries", "passed": False, "detail": str(e)})

    # ── Check 6: journaling log entries present ───────────────────────────────
    try:
        expected_dates = [f"2024-03-{str(d).zfill(2)}" for d in range(1, 16)]
        ok, detail = check_log_entries(habits_dir, "journal", expected_dates)
        checks.append({"name": "journaling_log_entries", "passed": ok, "detail": detail})
        if ok: total_score += 0.08
    except Exception as e:
        checks.append({"name": "journaling_log_entries", "passed": False, "detail": str(e)})

    # ── Check 7: exercise log entries present ────────────────────────────────
    try:
        expected_dates = [f"2024-03-{str(d).zfill(2)}" for d in range(1, 16)]
        ok, detail = check_log_entries(habits_dir, "exercise", expected_dates)
        checks.append({"name": "exercise_log_entries", "passed": ok, "detail": detail})
        if ok: total_score += 0.08
    except Exception as e:
        checks.append({"name": "exercise_log_entries", "passed": False, "detail": str(e)})

    # ── Check 8: client_calls frequency = weekdays ───────────────────────────
    try:
        ok, detail = check_frequency_in_file(habits_dir, "client_call", "weekday")
        checks.append({"name": "client_calls_weekday_frequency", "passed": ok, "detail": detail})
        if ok: total_score += 0.05
    except Exception as e:
        checks.append({"name": "client_calls_weekday_frequency", "passed": False, "detail": str(e)})

    # ── Check 9: journaling frequency = daily ────────────────────────────────
    try:
        ok, detail = check_frequency_in_file(habits_dir, "journal", "daily")
        checks.append({"name": "journaling_daily_frequency", "passed": ok, "detail": detail})
        if ok: total_score += 0.05
    except Exception as e:
        checks.append({"name": "journaling_daily_frequency", "passed": False, "detail": str(e)})

    # ── Check 10: exercise frequency = 3x/week ───────────────────────────────
    try:
        ok, detail = check_exercise_weekly_logic(habits_dir)
        checks.append({"name": "exercise_3x_week_frequency", "passed": ok, "detail": detail})
        if ok: total_score += 0.05
    except Exception as e:
        checks.append({"name": "exercise_3x_week_frequency", "passed": False, "detail": str(e)})

    # ── Check 11: Streak fields present in client_calls ──────────────────────
    try:
        ok, detail = check_streak_present(habits_dir, "client_call")
        checks.append({"name": "client_calls_streak_fields", "passed": ok, "detail": detail})
        if ok: total_score += 0.05
    except Exception as e:
        checks.append({"name": "client_calls_streak_fields", "passed": False, "detail": str(e)})

    # ── Check 12: Streak fields present in journaling ─────────────────────────
    try:
        ok, detail = check_streak_present(habits_dir, "journal")
        checks.append({"name": "journaling_streak_fields", "passed": ok, "detail": detail})
        if ok: total_score += 0.05
    except Exception as e:
        checks.append({"name": "journaling_streak_fields", "passed": False, "detail": str(e)})

    # ── Check 13: client_calls streak values (current=2, best=6) ─────────────
    try:
        exp_current, exp_best = compute_expected_streaks_client_calls()
        ok, detail = check_streak_values(habits_dir, "client_call", exp_current, exp_best)
        checks.append({
            "name": "client_calls_streak_values",
            "passed": ok,
            "detail": f"Expected current={exp_current}, best={exp_best}. {detail}"
        })
        if ok: total_score += 0.08
    except Exception as e:
        checks.append({"name": "client_calls_streak_values", "passed": False, "detail": str(e)})

    # ── Check 14: journaling streak values (current=3, best=8) ───────────────
    try:
        exp_current, exp_best = compute_expected_streaks_journaling()
        ok, detail = check_streak_values(habits_dir, "journal", exp_current, exp_best)
        checks.append({
            "name": "journaling_streak_values",
            "passed": ok,
            "detail": f"Expected current={exp_current}, best={exp_best}. {detail}"
        })
        if ok: total_score += 0.08
    except Exception as e:
        checks.append({"name": "journaling_streak_values", "passed": False, "detail": str(e)})

    # ── Check 15: summary.md completeness ────────────────────────────────────
    try:
        ok, detail = check_summary_file(habits_dir)
        checks.append({"name": "summary_md_completeness", "passed": ok, "detail": detail})
        if ok: total_score += 0.10
    except Exception as e:
        checks.append({"name": "summary_md_completeness", "passed": False, "detail": str(e)})

    # ── Final verdict ─────────────────────────────────────────────────────────
    total_score = round(min(total_score, 1.0), 4)
    passed_count = sum(1 for c in checks if c["passed"])
    overall_passed = total_score >= 0.70 and passed_count >= 10

    result = {
        "passed": overall_passed,
        "score": total_score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()