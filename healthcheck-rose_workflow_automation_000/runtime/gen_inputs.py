import os
import json
import random
from pathlib import Path
from datetime import datetime, timezone

random.seed(42)

workspace = Path(os.environ.get("WORKSPACE_DIR", "/workspace"))

# Create a realistic, deeply nested directory structure with distractor files
dirs = [
    workspace / "projects" / "wellness-app" / "src",
    workspace / "projects" / "wellness-app" / "tests",
    workspace / "projects" / "wellness-app" / "docs",
    workspace / "data" / "exports" / "2024",
    workspace / "data" / "exports" / "2023",
    workspace / "data" / "backups",
    workspace / "config" / "env",
    workspace / "scripts" / "utils",
    workspace / "logs" / "audit",
    workspace / "temp" / "staging",
    workspace / "tracker",  # This is where health-data.json should end up
]

for d in dirs:
    d.mkdir(parents=True, exist_ok=True)

# Distractor files to test contextual awareness
distractor_files = {
    workspace / "projects" / "wellness-app" / "src" / "app.js": "// main app entry point\nconsole.log('Wellness App v2.0');",
    workspace / "projects" / "wellness-app" / "src" / "utils.js": "// utility functions\nmodule.exports = {};",
    workspace / "projects" / "wellness-app" / "tests" / "app.test.js": "// unit tests\ndescribe('app', () => {});",
    workspace / "projects" / "wellness-app" / "docs" / "api.md": "# API Documentation\n\nEndpoints listed here.",
    workspace / "data" / "exports" / "2024" / "user_metrics.csv": "user_id,date,metric\n001,2024-01-01,42\n002,2024-01-02,55",
    workspace / "data" / "exports" / "2023" / "annual_report.json": json.dumps({"year": 2023, "total_users": 150, "avg_cups": 6.2}),
    workspace / "data" / "backups" / "backup_20240101.tar.gz.info": "Backup created: 2024-01-01 03:00:00",
    workspace / "config" / "env" / "production.env": "NODE_ENV=production\nPORT=3000\nDB_HOST=localhost",
    workspace / "config" / "env" / "development.env": "NODE_ENV=development\nPORT=3001\nDB_HOST=localhost",
    workspace / "scripts" / "utils" / "migrate.sh": "#!/bin/bash\necho 'Running migration...'",
    workspace / "logs" / "audit" / "access_2024.log": "2024-01-15 08:00:00 GET /api/health 200\n2024-01-15 08:01:00 POST /api/water 201",
    workspace / "temp" / "staging" / "draft_data.json": json.dumps({"draft": True, "water": [], "sleep": []}),
    # A red-herring health data file in wrong location
    workspace / "data" / "exports" / "2024" / "health-data.json": json.dumps({"water": [{"time": "2024-01-01T10:00:00.000Z", "cups": 99}], "sleep": []}),
}

for filepath, content in distractor_files.items():
    filepath.write_text(content)

# The task brief: leave the tracker directory empty (agent must create health-data.json there)
# Do NOT pre-create the health-data.json in the tracker directory

# Write a brief task context file (not a hint, just a reference note for the scenario)
brief = workspace / "TASK_BRIEF.txt"
brief.write_text(
    "Patient ID: PT-2047\n"
    "Assigned tracker directory: tracker/\n"
    "Health coach notes: Patient started logging on 2024-03-10.\n"
    "Needs historical records pre-populated before handoff.\n"
    "See wellness coordinator for exact record details.\n"
)

print("Workspace generated successfully.")
print(f"Tracker directory: {workspace / 'tracker'}")