import json
import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── directory structure with distractor files ──────────────────────────────
dirs = [
    "data",
    "scripts",
    "logs",
    "reports/weekly",
    "reports/monthly",
    "config",
    "nutrition/templates",
    "nutrition/logs",
    "backup/old",
    "tmp",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# distractor files
distractor_files = {
    "scripts/sync_wearable.py": "# placeholder for wearable device sync\ndef sync(): pass\n",
    "scripts/export_csv.py": "# CSV exporter stub\nimport csv\n",
    "logs/app.log": "2026-06-01 INFO: session started\n2026-06-01 INFO: user authenticated\n",
    "logs/errors.log": "2026-05-30 ERROR: timeout on nutrition API\n",
    "reports/weekly/week_21.txt": "Week 21: 3/4 workouts completed. Good consistency.\n",
    "reports/monthly/may_summary.txt": "May: 14 workouts, avg duration 52 min.\n",
    "config/app_settings.json": json.dumps({"theme": "dark", "units": "imperial", "notifications": True}, indent=2),
    "config/user_profile.yaml": "name: Jordan\nage: 29\nheight_cm: 178\n",
    "nutrition/templates/meal_plan.txt": "Monday: oatmeal, chicken salad, salmon bowl\n",
    "nutrition/logs/may_meals.csv": "date,meal,calories\n2026-05-28,lunch,700\n2026-05-29,dinner,820\n",
    "backup/old/fitness_v1.json": json.dumps({"workouts": [], "meals": [], "prs": {}}, indent=2),
    "tmp/scratch.txt": "rough notes: need to log last 3 sessions\n",
}
for rel_path, content in distractor_files.items():
    (workspace / rel_path).write_text(content)

# ── THE MAIN DATA FILE: pre-seeded with existing state ────────────────────
# PRs are seeded so that some exercises will be beaten and some won't.
# Bench Press current PR 1RM = 210.0  (185 × (1+5/30) = 185×1.1667 = 215.83 → will beat it)
# Overhead Press current PR 1RM = 145.0 (115 × (1+8/30) = 115×1.2667 = 145.67 → will barely beat it)
# Squat current PR 1RM = 290.0 (225 × (1+10/30) = 225×1.3333 = 300 → will beat it)
# Deadlift current PR 1RM = 340.0 (275 × (1+8/30) = 275×1.2667 = 348.33 → will beat it)
# Tricep Pushdown — no existing PR (new PR will be set)

fitness_data = {
    "profile": {
        "goal": "Build strength and muscle",
        "weight_log": [
            {"date": "2026-05-01", "weight_lbs": 185},
            {"date": "2026-05-15", "weight_lbs": 184},
        ],
        "start_date": "2026-01-01"
    },
    "workouts": [
        {
            "date": "2026-06-01",
            "type": "strength",
            "muscle_groups": ["legs"],
            "exercises": [
                {"name": "Squat", "sets": [{"weight": 205, "reps": 8}, {"weight": 205, "reps": 7}]}
            ],
            "duration_min": 55,
            "notes": ""
        },
        {
            "date": "2026-06-03",
            "type": "cardio",
            "muscle_groups": ["cardiovascular"],
            "exercises": [],
            "duration_min": 30,
            "notes": "5k run, 29 minutes"
        }
    ],
    "meals": [
        {
            "date": "2026-06-01",
            "meal": "lunch",
            "description": "Grilled chicken with sweet potato",
            "estimated_calories": 600,
            "estimated_protein_g": 48,
            "time": "12:00"
        }
    ],
    "prs": {
        "Bench Press":      {"1rm": 210.0,  "date": "2026-04-15", "weight": 180, "reps": 5},
        "Overhead Press":   {"1rm": 145.0,  "date": "2026-05-10", "weight": 110, "reps": 8},
        "Squat":            {"1rm": 290.0,  "date": "2026-05-20", "weight": 220, "reps": 8},
        "Deadlift":         {"1rm": 340.0,  "date": "2026-05-18", "weight": 260, "reps": 8},
    },
    "weekly_summary": [
        {
            "week_start": "2026-05-26",
            "workout_count": 4,
            "target": 4,
            "notes": "Great week, hit all targets"
        }
    ],
    "current_week": {
        "workout_count": 2,
        "target": 4,
        "workouts": ["2026-06-01", "2026-06-03"]
    }
}

(workspace / "data" / "fitness.json").write_text(json.dumps(fitness_data, indent=2))

# ── Raw workout notes the agent must process (messy natural language) ─────
raw_notes = """
SESSION NOTES — Week of June 2, 2026
======================================

[Monday June 2 - Upper Body A]
bench 185x5 185x5 185x4
overhead press 115x8 115x7 115x6
tricep pushdowns 50x12 x3
duration: about 65 minutes

[Wednesday June 4 - Legs]
squat 225x10 225x8 225x6
deadlift 275x8 275x6
did some stretching after
duration: 70 min

[Friday June 6 - Cardio + Arms]
went for a 5k run, 27 minutes
curls 45x10 45x10
duration: 45 minutes

MEAL NOTE (Wednesday June 4):
Post-workout: protein shake after gym
Dinner: had chipotle for dinner

NOTE: Jordan mentioned left knee felt a bit sore after squats Wednesday.
"""

(workspace / "tmp" / "raw_session_notes.txt").write_text(raw_notes)

print("Workspace generated successfully.")
print(f"Key file: {workspace / 'data' / 'fitness.json'}")
print(f"Raw notes: {workspace / 'tmp' / 'raw_session_notes.txt'}")