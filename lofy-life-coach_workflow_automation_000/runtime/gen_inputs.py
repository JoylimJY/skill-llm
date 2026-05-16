import json
import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "data",
    "logs/2024",
    "logs/2025",
    "config",
    "scripts",
    "archive/week_2025_20",
    "archive/week_2025_21",
    "docs",
    "tmp",
    "briefings",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────
(workspace / "config" / "app_settings.json").write_text(json.dumps({
    "theme": "dark", "notifications": True, "timezone": "America/New_York"
}, indent=2))

(workspace / "config" / "nudge_schedule.txt").write_text(
    "morning: 07:00\nevening: 21:00\nsleep_reminder: 23:30\n"
)

(workspace / "scripts" / "sync_calendar.py").write_text(
    "# Placeholder: calendar sync not yet implemented\npass\n"
)

(workspace / "scripts" / "weather_fetch.sh").write_text(
    "#!/bin/bash\ncurl -s wttr.in/$1\n"
)

(workspace / "logs" / "2024" / "activity_raw.txt").write_text(
    "2024-12-01: workout\n2024-12-03: workout\n2024-12-05: workout\n"
)

(workspace / "logs" / "2025" / "activity_raw.txt").write_text(
    "2025-05-12: workout\n2025-05-13: read\n2025-05-15: meal_prep\n"
)

(workspace / "docs" / "habit_definitions.txt").write_text(
    "sleep_by_midnight: in bed before 00:00\n"
    "meal_prep_sunday: batch-cook meals on Sunday\n"
    "read_30min: read a book for at least 30 minutes\n"
)

(workspace / "docs" / "weekly_targets.txt").write_text(
    "fitness: 4 sessions per week\n"
    "habits: all 3 daily\n"
)

(workspace / "tmp" / "pending_updates.txt").write_text(
    "Mon: worked out\n"
    "Tue: read 30min, slept by midnight\n"
    "Wed: worked out, meal prep (wrong day but logged)\n"
    "Thu: read 30min\n"
    "Fri: worked out\n"
    "Sat: slept by midnight, read 30min\n"
    "Sun: worked out, did meal prep, read 30min, slept by midnight\n"
    "Career: applied to Stripe on Wed, applied to Notion on Fri\n"
)

(workspace / "briefings" / "morning_2025_05_18.txt").write_text(
    "Good morning! You have a gym session and a portfolio review today.\n"
    "Streak: 2 weeks hitting fitness target.\n"
)

(workspace / "archive" / "week_2025_20" / "goals_snapshot.json").write_text(json.dumps({
    "fitness": {"weekly_count": 4, "streak_weeks_hit": 2},
    "habits": {"weekly_completion_rate": 0.67}
}, indent=2))

(workspace / "archive" / "week_2025_21" / "goals_snapshot.json").write_text(json.dumps({
    "fitness": {"weekly_count": 3, "streak_weeks_hit": 2},
    "habits": {"weekly_completion_rate": 0.57}
}, indent=2))

(workspace / "logs" / "2025" / "career_notes.txt").write_text(
    "Stripe - applied 2025-05-21\nNotion - applied 2025-05-23\n"
    "Stripe - interview scheduled 2025-05-28\n"
)

# ── MAIN DATA FILE (messy / stale state) ─────────────────────────────────────
# This represents end-of-previous-week state (stale, partially wrong)
# Current week: Mon 2025-05-19 through Sun 2025-05-25
# The agent must apply this week's updates and then run weekly reset

goals = {
    "fitness": {
        "target": "Run or gym 4x per week",
        "weekly_target": 4,
        "current_week_count": 0,       # STALE — needs this week's workouts applied
        "streak_weeks_hit": 2,          # from previous weeks
        "last_workout_date": "2025-05-18"  # last Sunday of prev week
    },
    "career": {
        "target": "Land a senior engineer role at a product company",
        "total_apps_sent": 7,           # pre-existing count
        "interviews_completed": 1,
        "offers": 0
    },
    "habits": {
        "tracked": ["sleep_by_midnight", "meal_prep_sunday", "read_30min"],
        "today": {},                    # empty — needs today (Sunday) filled in
        "streaks": {
            "sleep_by_midnight": 3,     # consecutive days streak (pre-week)
            "meal_prep_sunday": 1,
            "read_30min": 4
        },
        "weekly_completion_rate": 0.0  # stale, needs recalc
    },
    "daily_log": [
        {"date": "2025-05-12", "note": "Good week overall"},
        {"date": "2025-05-18", "note": "End of week 20, missed one workout"}
    ]
}

(workspace / "data" / "goals.json").write_text(json.dumps(goals, indent=2))

print("Workspace generated successfully.")
print("data/goals.json written with stale state.")
print("tmp/pending_updates.txt contains this week's activity log.")