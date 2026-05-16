import os
import json
import random
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# --- Clone the habit-tracker skill ---
os.system("git clone https://github.com/tianhm/habits-tracker.git /workspace/habit-tracker 2>/dev/null || true")

# Create deeply nested distractor directory structure
dirs = [
    "workspace/wellness_program/q1_reports",
    "workspace/wellness_program/employee_data/raw",
    "workspace/wellness_program/employee_data/processed",
    "workspace/wellness_program/templates",
    "workspace/hr_docs/policies",
    "workspace/hr_docs/onboarding",
    "workspace/analytics/dashboards",
    "workspace/analytics/exports",
    "workspace/configs/legacy",
    "workspace/configs/active",
    "workspace/scripts/archive",
    "workspace/scripts/utils",
    "workspace/backups/2024",
    "workspace/backups/2023",
    "workspace/notes",
]

for d in dirs:
    Path(d).mkdir(parents=True, exist_ok=True)

# Distractor files (plausible but irrelevant)
distractor_files = {
    "workspace/wellness_program/q1_reports/summary_q1.csv": "employee_id,habit,completions\n001,Exercise,18\n001,Meditation,12\n",
    "workspace/wellness_program/employee_data/raw/employee_001.json": json.dumps({
        "id": "001", "name": "Jordan Lee", "start_date": "2024-01-15", "program": "standard"
    }, indent=2),
    "workspace/wellness_program/employee_data/processed/onboarding_checklist.txt": "[ ] Setup habit tracker\n[ ] Complete orientation\n[ ] Schedule 1:1\n",
    "workspace/wellness_program/templates/weekly_template.md": "# Weekly Wellness Report\n\n## Habits Tracked:\n- Morning Exercise\n- Reading\n- Meditation\n",
    "workspace/hr_docs/policies/wellness_policy_v2.txt": "All employees enrolled in the wellness program must track at least 3 habits per quarter.\nReporting frequency: weekly.\nMinimum streak target: 5 days.\n",
    "workspace/hr_docs/onboarding/new_hire_guide.txt": "Welcome to the wellness program.\nYou will be tracking three core habits:\n1. Morning Walk (daily)\n2. Reading (daily)\n3. Weekly Review (weekly)\n",
    "workspace/analytics/dashboards/kpi_definitions.json": json.dumps({
        "completion_rate_target": 0.80,
        "streak_target": 7,
        "reporting_period_days": 30
    }, indent=2),
    "workspace/analytics/exports/export_schema.txt": "Fields: habit_name, date, count, note, streak\n",
    "workspace/configs/legacy/old_tracker_config.json": json.dumps({
        "version": "0.1", "habits": [], "deprecated": True
    }, indent=2),
    "workspace/configs/active/program_config.json": json.dumps({
        "program": "30-day-wellness",
        "start": "2024-03-01",
        "habits": [
            {"name": "Morning Walk", "freq": "daily"},
            {"name": "Reading", "freq": "daily"},
            {"name": "Weekly Review", "freq": "weekly"}
        ]
    }, indent=2),
    "workspace/scripts/archive/migrate_v1.sh": "#!/bin/bash\n# Legacy migration script - DO NOT USE\necho 'Deprecated'\n",
    "workspace/scripts/utils/check_node.sh": "#!/bin/bash\nnode --version\n",
    "workspace/backups/2024/habits_backup_jan.json": json.dumps({"habits": [], "logs": [], "backup_date": "2024-01-31"}, indent=2),
    "workspace/backups/2023/habits_backup_dec.json": json.dumps({"habits": [], "logs": [], "backup_date": "2023-12-31"}, indent=2),
    "workspace/notes/tracker_research.txt": "Options evaluated:\n- Habitica (web, requires account)\n- Loop Habit Tracker (Android only)\n- habits-tracker (CLI, local storage)\nDecision: Use habits-tracker CLI\n",
}

for filepath, content in distractor_files.items():
    p = Path(filepath)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)

# --- Generate the self-reported historical data file for the agent to use ---
# This simulates a new hire's self-reported logs for the past 28 days
# The agent must read this and backdate log entries

today = datetime(2024, 4, 15)  # Fixed reference date for determinism
start_date = today - timedelta(days=27)  # 28-day window (day 0 to day 27)

# Morning Walk: daily habit, target 1
# Self-reported: completed on 22 out of 28 days (specific days missed)
missed_walk_offsets = {3, 7, 10, 14, 18, 22}  # 6 days missed
walk_logs = []
for i in range(28):
    d = start_date + timedelta(days=i)
    if i not in missed_walk_offsets:
        walk_logs.append({"date": d.strftime("%Y-%m-%d"), "count": 1, "note": "completed"})

# Reading: daily habit, target 1
# Self-reported: completed on 18 out of 28 days
missed_reading_offsets = {0, 1, 5, 8, 12, 15, 16, 20, 23, 27}  # 10 days missed
reading_logs = []
for i in range(28):
    d = start_date + timedelta(days=i)
    if i not in missed_reading_offsets:
        reading_logs.append({"date": d.strftime("%Y-%m-%d"), "count": 1, "note": "completed"})

# Weekly Review: weekly habit, target 1 per week
# 4 weeks in 28 days, completed in weeks 1, 2, 4 (missed week 3)
week_review_dates = [
    (start_date + timedelta(days=6)).strftime("%Y-%m-%d"),   # end of week 1
    (start_date + timedelta(days=13)).strftime("%Y-%m-%d"),  # end of week 2
    # week 3 missed
    (start_date + timedelta(days=27)).strftime("%Y-%m-%d"),  # end of week 4
]
weekly_review_logs = [{"date": d, "count": 1, "note": "completed"} for d in week_review_dates]

self_reported = {
    "reference_date": today.strftime("%Y-%m-%d"),
    "period_days": 28,
    "habits": [
        {
            "name": "Morning Walk",
            "frequency": "daily",
            "target": 1,
            "reminder": "07:00",
            "description": "15-minute morning walk outside",
            "logs": walk_logs
        },
        {
            "name": "Reading",
            "frequency": "daily",
            "target": 1,
            "reminder": "21:30",
            "description": "Read non-fiction for at least 20 minutes",
            "logs": reading_logs
        },
        {
            "name": "Weekly Review",
            "frequency": "weekly",
            "target": 1,
            "reminder": "18:00",
            "description": "Sunday evening review of the week",
            "logs": weekly_review_logs
        }
    ]
}

sr_path = Path("workspace/wellness_program/employee_data/raw/jordan_self_reported_28days.json")
sr_path.write_text(json.dumps(self_reported, indent=2))

print("Workspace generated successfully.")
print(f"Self-reported data written to: {sr_path}")
print(f"Reference date: {today.strftime('%Y-%m-%d')}")
print(f"Period start: {start_date.strftime('%Y-%m-%d')}")