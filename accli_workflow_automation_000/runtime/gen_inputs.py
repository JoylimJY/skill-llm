import os
import json
import random

random.seed(42)

workspace = "/workspace"

# Create a realistic deeply-nested project directory structure with distractor files
dirs = [
    "sprint_planning/docs",
    "sprint_planning/notes",
    "sprint_planning/archive",
    "team_calendar/exports",
    "team_calendar/backups",
    "stakeholder_mgmt/contacts",
    "stakeholder_mgmt/reports",
    "retrospectives/q1",
    "retrospectives/q2",
    "meeting_minutes/january",
    "meeting_minutes/february",
    "scripts/utilities",
    "config/profiles",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "sprint_planning/docs/sprint_42_goals.md": "# Sprint 42 Goals\n- Finalize API integration\n- Deploy staging environment\n- Code review backlog clearance\n",
    "sprint_planning/notes/velocity_notes.txt": "Team velocity: 34 points average. Watch for holiday impact in February.\n",
    "sprint_planning/archive/sprint_41_retro.md": "## Sprint 41 Retrospective\nWhat went well: CI/CD pipeline improvements.\nWhat didn't: Too many unplanned interruptions.\n",
    "team_calendar/exports/calendar_export_old.csv": "Subject,Start Date,End Date\nTeam Sync,2024-12-01,2024-12-01\nHoliday,2024-12-25,2024-12-25\n",
    "team_calendar/backups/backup_manifest.json": json.dumps({"last_backup": "2025-01-10T08:00:00", "calendars": ["Work", "Personal", "Engineering"]}),
    "stakeholder_mgmt/contacts/stakeholders.csv": "Name,Email,Role\nAlice Johnson,alice@example.com,Product Owner\nBob Martinez,bob@example.com,CTO\nCaroline Lee,caroline@example.com,Scrum Master\n",
    "stakeholder_mgmt/reports/q4_summary.txt": "Q4 stakeholder satisfaction: 87%. Key concerns: release cadence and communication frequency.\n",
    "retrospectives/q1/q1_action_items.md": "- Set up recurring engineering all-hands\n- Improve on-call rotation documentation\n- Schedule architecture review sessions\n",
    "retrospectives/q2/q2_outcomes.json": json.dumps({"outcomes": ["Reduced P0 incidents by 40%", "Launched feature flags system"], "next_steps": ["Continue monitoring", "Plan Q3 roadmap"]}),
    "meeting_minutes/january/jan_15_standup.txt": "Attendees: Dev team\nDecisions: Move sprint demo to Thursday.\nAction items: Update Jira board.\n",
    "meeting_minutes/february/feb_03_planning.txt": "Attendees: PM, Tech Lead, QA Lead\nAgenda: Sprint 43 scope definition\nDecisions: Include performance testing in definition of done.\n",
    "scripts/utilities/parse_events.py": "#!/usr/bin/env python3\n# Utility to parse calendar exports\nimport csv\nimport sys\n\ndef parse(filepath):\n    with open(filepath) as f:\n        reader = csv.DictReader(f)\n        return list(reader)\n\nif __name__ == '__main__':\n    print(parse(sys.argv[1]))\n",
    "config/profiles/default_profile.json": json.dumps({"user": "project_coordinator", "timezone": "America/Los_Angeles", "work_hours": {"start": "09:00", "end": "18:00"}}),
    "config/profiles/team_settings.yaml": "team_name: Engineering Alpha\ndefault_meeting_duration: 60\nnotification_lead_time: 15\n",
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w") as f:
        f.write(content)

# Create the task brief file - gives context but no hints about CLI usage
task_brief = {
    "task": "Sprint Planning & Stakeholder Sync Scheduling",
    "date": "2025-03-10",
    "target_date": "2025-03-12",
    "sprint_meeting": {
        "title": "Sprint 43 Planning Session",
        "duration_minutes": 90,
        "preferred_window": "09:00-18:00",
        "location": "Engineering War Room",
        "description": "Kickoff planning for Sprint 43. All engineers required.",
        "target_calendar": "Engineering"
    },
    "existing_event_update": {
        "search_query": "Stakeholder Sync",
        "calendar": "Work",
        "new_description": "Updated: Video call via Zoom at https://zoom.us/j/999888777. Passcode: sprint43",
        "target_date_range_from": "2025-03-10",
        "target_date_range_to": "2025-03-14"
    },
    "output_file": "meeting_report.json"
}

with open(os.path.join(workspace, "task_brief.json"), "w") as f:
    json.dump(task_brief, f, indent=2)

print("Workspace generated successfully.")