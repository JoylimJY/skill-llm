import json
import sys
from pathlib import Path

def load_goals(workspace):
    p = Path(workspace) / "data" / "goals.json"
    with open(p) as f:
        return json.load(f)

def run_checks(workspace):
    checks = []
    score_parts = []

    try:
        goals = load_goals(workspace)
    except Exception as e:
        return [{"name": "goals_json_readable", "passed": False, "detail": str(e)}], 0.0

    # ── CHECK 1: Fitness — current_week_count should be 0 after reset ─────────
    # The agent must apply 4 workouts (Mon, Wed, Fri, Sun) then RESET to 0
    # After weekly reset, current_week_count resets to 0
    try:
        cwc = goals["fitness"]["current_week_count"]
        passed = cwc == 0
        checks.append({
            "name": "fitness_current_week_count_reset_to_0",
            "passed": passed,
            "detail": f"current_week_count={cwc}, expected 0 after weekly reset"
        })
        score_parts.append(1.0 if passed else 0.0)
    except Exception as e:
        checks.append({"name": "fitness_current_week_count_reset_to_0", "passed": False, "detail": str(e)})
        score_parts.append(0.0)

    # ── CHECK 2: Streak weeks — previous was 2, this week hit target (4 workouts >= 4) → should be 3 ──
    try:
        swh = goals["fitness"]["streak_weeks_hit"]
        passed = swh == 3
        checks.append({
            "name": "fitness_streak_weeks_hit_incremented",
            "passed": passed,
            "detail": f"streak_weeks_hit={swh}, expected 3 (was 2, this week hit 4/4 target)"
        })
        score_parts.append(1.0 if passed else 0.0)
    except Exception as e:
        checks.append({"name": "fitness_streak_weeks_hit_incremented", "passed": False, "detail": str(e)})
        score_parts.append(0.0)

    # ── CHECK 3: last_workout_date updated to Sunday 2025-05-25 ──────────────
    try:
        lwd = goals["fitness"].get("last_workout_date", "")
        passed = lwd == "2025-05-25"
        checks.append({
            "name": "fitness_last_workout_date_updated",
            "passed": passed,
            "detail": f"last_workout_date='{lwd}', expected '2025-05-25'"
        })
        score_parts.append(1.0 if passed else 0.0)
    except Exception as e:
        checks.append({"name": "fitness_last_workout_date_updated", "passed": False, "detail": str(e)})
        score_parts.append(0.0)

    # ── CHECK 4: Career apps — was 7, applied to Stripe + Notion = +2 → 9 ────
    try:
        apps = goals["career"]["total_apps_sent"]
        passed = apps == 9
        checks.append({
            "name": "career_total_apps_sent",
            "passed": passed,
            "detail": f"total_apps_sent={apps}, expected 9 (7 + 2 new)"
        })
        score_parts.append(1.0 if passed else 0.0)
    except Exception as e:
        checks.append({"name": "career_total_apps_sent", "passed": False, "detail": str(e)})
        score_parts.append(0.0)

    # ── CHECK 5: Today's habits (Sunday) — all 3 logged ──────────────────────
    try:
        today = goals["habits"].get("today", {})
        # Sunday: meal_prep_sunday=True, read_30min=True, sleep_by_midnight=True
        meal = today.get("meal_prep_sunday", False)
        read = today.get("read_30min", False)
        sleep = today.get("sleep_by_midnight", False)
        passed = bool(meal) and bool(read) and bool(sleep)
        checks.append({
            "name": "habits_today_all_three_logged",
            "passed": passed,
            "detail": f"today habits: meal_prep={meal}, read_30min={read}, sleep_by_midnight={sleep}"
        })
        score_parts.append(1.0 if passed else 0.0)
    except Exception as e:
        checks.append({"name": "habits_today_all_three_logged", "passed": False, "detail": str(e)})
        score_parts.append(0.0)

    # ── CHECK 6: weekly_completion_rate is non-zero and reasonable (>0.5) ────
    # Week has 7 days × 3 habits = 21 possible
    # Logged: Mon(workout only→0 habits in today format), Tue(read+sleep=2),
    #         Wed(read? no—only workout+meal logged for Wed), Thu(read=1),
    #         Fri(sleep+read? only sleep logged), Sat(sleep+read=2), Sun(all3=3)
    # The exact number depends on interpretation; we just check it's been calculated (>0, <=1)
    try:
        rate = goals["habits"].get("weekly_completion_rate", 0)
        passed = isinstance(rate, (int, float)) and 0 < rate <= 1.0
        checks.append({
            "name": "habits_weekly_completion_rate_calculated",
            "passed": passed,
            "detail": f"weekly_completion_rate={rate}, expected a value in (0, 1]"
        })
        score_parts.append(1.0 if passed else 0.0)
    except Exception as e:
        checks.append({"name": "habits_weekly_completion_rate_calculated", "passed": False, "detail": str(e)})
        score_parts.append(0.0)

    # ── CHECK 7: daily_log has a new entry for 2025-05-25 ────────────────────
    try:
        daily_log = goals.get("daily_log", [])
        dates = [entry.get("date", "") for entry in daily_log]
        passed = "2025-05-25" in dates
        checks.append({
            "name": "daily_log_has_sunday_entry",
            "passed": passed,
            "detail": f"daily_log dates found: {dates}"
        })
        score_parts.append(1.0 if passed else 0.0)
    except Exception as e:
        checks.append({"name": "daily_log_has_sunday_entry", "passed": False, "detail": str(e)})
        score_parts.append(0.0)

    # ── CHECK 8: Archive — a new archive entry for week 2025-22 was created ──
    try:
        archive_candidates = list(Path(workspace).rglob("*week_2025_22*"))
        # Also accept any snapshot file with 2025-05-25 or week22 content
        found = len(archive_candidates) > 0
        if not found:
            # Check if any archive folder newer than week_21 exists
            all_archives = list((Path(workspace) / "archive").iterdir())
            found = any("22" in str(a) or "2025-05-25" in str(a) for a in all_archives)
        checks.append({
            "name": "weekly_archive_created",
            "passed": found,
            "detail": f"Archive for week 2025-22 found: {found}. Candidates: {[str(c) for c in archive_candidates]}"
        })
        score_parts.append(1.0 if found else 0.0)
    except Exception as e:
        checks.append({"name": "weekly_archive_created", "passed": False, "detail": str(e)})
        score_parts.append(0.0)

    # ── CHECK 9: Habit streaks updated — read_30min was 4, appeared Tue/Thu/Sat/Sun → should be ≥5
    try:
        streaks = goals["habits"].get("streaks", {})
        read_streak = streaks.get("read_30min", 0)
        passed = read_streak >= 5
        checks.append({
            "name": "habit_streak_read_30min_incremented",
            "passed": passed,
            "detail": f"read_30min streak={read_streak}, expected >=5 (was 4, continued this week)"
        })
        score_parts.append(1.0 if passed else 0.0)
    except Exception as e:
        checks.append({"name": "habit_streak_read_30min_incremented", "passed": False, "detail": str(e)})
        score_parts.append(0.0)

    # ── CHECK 10: Nudge logic — no invalid fitness nudge (workout done today) ──
    # Check that any generated nudge file (if exists) does NOT fire a gym nudge for today
    try:
        nudge_files = list(Path(workspace).rglob("*nudge*"))
        bad_nudge = False
        for nf in nudge_files:
            content = nf.read_text().lower()
            if "gym" in content or "workout" in content or "exercise" in content:
                bad_nudge = True
        passed = not bad_nudge
        checks.append({
            "name": "no_invalid_gym_nudge_when_workout_done",
            "passed": passed,
            "detail": f"Gym nudge incorrectly fired in nudge files: {[str(n) for n in nudge_files]}" if bad_nudge else "No invalid gym nudge found."
        })
        score_parts.append(1.0 if passed else 0.0)
    except Exception as e:
        checks.append({"name": "no_invalid_gym_nudge_when_workout_done", "passed": False, "detail": str(e)})
        score_parts.append(0.0)

    final_score = sum(score_parts) / len(score_parts) if score_parts else 0.0
    return checks, round(final_score, 3)


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks, score = run_checks(workspace)
    passed = score >= 0.70

    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()