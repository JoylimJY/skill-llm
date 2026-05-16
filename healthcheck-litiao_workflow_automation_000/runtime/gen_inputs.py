import os
import json
import random

random.seed(42)

workspace = "/workspace"

# Create a realistic, deeply nested directory structure with distractor files
dirs = [
    "health-tracker",
    "health-tracker/reports",
    "health-tracker/reports/weekly",
    "health-tracker/reports/monthly",
    "health-tracker/backups",
    "health-tracker/config",
    "projects/wellness-app",
    "projects/wellness-app/src",
    "projects/wellness-app/tests",
    "notes",
    "logs",
    "logs/archive",
    "tmp",
    "tmp/scratch",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "health-tracker/reports/weekly/week-01-summary.txt": "Week 1: 14 cups water, 49 hrs sleep\n",
    "health-tracker/reports/weekly/week-02-summary.txt": "Week 2: 21 cups water, 52 hrs sleep\n",
    "health-tracker/reports/monthly/january.csv": "date,cups,sleep_hours\n2024-01-01,3,7.5\n2024-01-02,4,8.0\n",
    "health-tracker/backups/health-data-backup-2024-01-01.json": json.dumps({
        "water": [{"time": "2024-01-01T08:00:00.000Z", "cups": 2}],
        "sleep": [{"time": "2024-01-01T22:00:00.000Z", "action": "sleep"},
                  {"time": "2024-01-02T06:00:00.000Z", "action": "wake"}]
    }),
    "health-tracker/config/settings.ini": "[tracker]\nunit=cups\ntz=UTC\nreminder=true\n",
    "health-tracker/config/thresholds.json": json.dumps({"daily_water_goal": 8, "sleep_goal_hours": 8}),
    "projects/wellness-app/src/tracker.js": "// Legacy tracker - deprecated\nconst GOAL = 8;\n",
    "projects/wellness-app/src/utils.js": "function toISO(d) { return d.toISOString(); }\nmodule.exports = { toISO };\n",
    "projects/wellness-app/tests/tracker.test.js": "const assert = require('assert');\n// TODO: write tests\n",
    "notes/hydration-goals.txt": "Daily goal: drink at least 8 cups of water\nSleep goal: 7-9 hours per night\n",
    "notes/routine.md": "# Morning Routine\n- Wake up 6am\n- Drink 2 cups water\n- Exercise 30min\n",
    "logs/activity.log": "2024-01-15 09:00:00 - app started\n2024-01-15 09:01:00 - user logged in\n",
    "logs/archive/2024-01-14.log": "2024-01-14 22:00:00 - sleep recorded\n2024-01-14 06:00:00 - wake recorded\n",
    "tmp/scratch/draft-notes.txt": "water: 3 cups this morning\nneed to log sleep properly\n",
    "tmp/old-data.json": json.dumps({"records": [], "version": "0.1"}),
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w") as f:
        f.write(content)

# IMPORTANT: Do NOT create health-tracker/health-data.json
# The agent must create it from scratch using the skill's commands.

# Create a task specification file that gives the business context
task_spec = {
    "task": "Set up health tracking log",
    "base_directory": "/workspace/health-tracker",
    "events_to_log": [
        {"event": "drank 3 cups of water"},
        {"event": "drank 2 cups of water"},
        {"event": "went to sleep"},
        {"event": "woke up"},
        {"event": "drank 5 cups of water"},
        {"event": "correction: last water entry should be 4 cups, not 5"},
        {"event": "removal: the very first water entry was a mistake, delete it"}
    ],
    "expected_final_state": "health-data.json in base_directory with correct records"
}

with open(os.path.join(workspace, "health-tracker/task-spec.json"), "w") as f:
    json.dump(task_spec, f, indent=2)

print("Workspace initialized successfully.")
print(f"Distractor files created: {len(distractor_files)}")
print("health-data.json NOT pre-created (agent must create it)")