import os
import csv
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create a realistic, deeply nested project directory structure with distractor files
dirs = [
    "project/docs",
    "project/src/api",
    "project/src/frontend",
    "project/src/backend",
    "project/tests/unit",
    "project/tests/integration",
    "project/planning/q1",
    "project/planning/q2",
    "project/planning/retrospectives",
    "project/infra/terraform",
    "project/infra/docker",
    ".config",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "project/docs/architecture.md": "# Architecture\n\nThis document describes the system architecture for the 2026 platform.\n\n## Components\n- API Gateway\n- Auth Service\n- Data Pipeline\n",
    "project/docs/onboarding.md": "# Team Onboarding\n\nWelcome to the team. Please read all docs before starting.\n",
    "project/src/api/routes.py": "# Auto-generated routes file\n\nfrom flask import Blueprint\nroutes = Blueprint('routes', __name__)\n",
    "project/src/frontend/app.js": "// Main frontend application entry\nconsole.log('App starting...');\n",
    "project/src/backend/main.py": "# Backend main module\ndef main():\n    pass\n",
    "project/tests/unit/test_utils.py": "import pytest\n\ndef test_placeholder():\n    assert True\n",
    "project/tests/integration/test_api.py": "import pytest\n\ndef test_api_health():\n    assert True\n",
    "project/planning/q1/sprint_log.txt": "Q1 Sprint Log\n=============\nSprint 1: Completed API scaffold\nSprint 2: Auth service deployed\nSprint 3: Data pipeline v1\n",
    "project/planning/retrospectives/retro_jan.txt": "January Retrospective\n---------------------\nWhat went well: Good velocity\nWhat to improve: More documentation\n",
    "project/infra/terraform/main.tf": '# Terraform main config\nprovider "aws" {\n  region = "eu-central-1"\n}\n',
    "project/infra/docker/Dockerfile.api": "FROM python:3.11-slim\nWORKDIR /app\nCOPY . .\nRUN pip install -r requirements.txt\n",
    ".config/settings.json": '{"theme": "dark", "editor": "vscode", "autosave": true}',
    "project/planning/q2/notes.txt": "Q2 Planning Notes\n-----------------\nFocus areas:\n- Feature X release\n- Performance optimization\n- Team alignment sessions\n- Code cleanup\n",
}
for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w") as f:
        f.write(content)

# Create an older, misleading sprint mapping file (uses standard 14-day sprints - WRONG system)
old_sprint_map = {
    "note": "DEPRECATED - old 14-day sprint mapping, do not use for 2026 planning",
    "sprint_length_days": 14,
    "year_2026_sprint_1_start": "2026-01-01",
    "system": "standard_scrum",
}
with open(os.path.join(workspace, "project/planning/q2/old_sprint_map.json"), "w") as f:
    json.dump(old_sprint_map, f, indent=2)

# Create a misleading tone reference that uses wrong tone associations (trap for naive agents)
wrong_tone_ref = {
    "note": "DRAFT - incorrect draft, do not use",
    "tone_1_name": "Lunar",  # WRONG - should be Magnetic
    "tone_2_name": "Magnetic",  # WRONG
    "sprint_start_tone": 1,  # WRONG - 2026 starts on Tone 10
    "draft_author": "intern",
    "status": "rejected",
}
with open(os.path.join(workspace, "project/planning/q2/tone_draft_REJECTED.json"), "w") as f:
    json.dump(wrong_tone_ref, f, indent=2)

# THE ACTUAL INPUT: milestone_dates.csv
# 12 project milestone dates in Q2 2026 (April–June)
# Carefully chosen to hit sprint boundaries, reflection phases, and edge cases
milestone_dates = [
    # date, event_description
    ("2026-04-01", "Q2 kickoff planning session"),        # Tone 9, Sprint 7 - last day of sprint 7 (boundary)
    ("2026-04-02", "Begin coding feature branch"),        # Tone 10, Sprint 8 - new sprint starts (boundary trap)
    ("2026-04-06", "Goal definition workshop"),           # Tone 1, Sprint 8 - ideal goal setting
    ("2026-04-12", "Sunday collaboration with partners"), # Tone 7, Sprint 8 - ideal meeting day
    ("2026-04-15", "Release candidate deployment"),       # Tone 10, Sprint 9 - action/release day
    ("2026-04-19", "Align new sprint goal"),              # Tone 1, Sprint 9
    ("2026-04-28", "Demo day for stakeholders"),          # Tone 10, Sprint 10
    ("2026-05-01", "End of sprint activities"),           # Tone 13, Sprint 10 - reflection phase
    ("2026-05-11", "New sprint kickoff"),                 # Tone 10, Sprint 11 - another sprint start
    ("2026-05-15", "Goal alignment for May sprint"),      # Tone 1, Sprint 11
    ("2026-06-06", "June release day"),                   # Tone 10, Sprint 13
    ("2026-06-16", "Team sync for June partner review"),  # Tone 7, Sprint 13
]

csv_path = os.path.join(workspace, "project/planning/q2/milestone_dates.csv")
with open(csv_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["date", "event_description"])
    for date, desc in milestone_dates:
        writer.writerow([date, desc])

print("Workspace generated successfully.")
print(f"Input file: {csv_path}")
print(f"Total milestone dates: {len(milestone_dates)}")