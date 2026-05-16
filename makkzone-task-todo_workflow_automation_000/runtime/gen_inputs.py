import os
import random
import json
import csv

random.seed(42)

base = "/workspace"

# ── distractor directory structure ──────────────────────────────────────────
dirs = [
    "docs/architecture",
    "docs/retrospectives",
    "reports/q1",
    "reports/q2",
    "config/environments",
    "config/db",
    "scripts/migration",
    "scripts/backup",
    "src/core",
    "src/integrations",
    "tests/unit",
    "tests/integration",
]
for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

distractor_files = {
    "docs/architecture/system_design.md": "# System Design\nSee confluence for details.\n",
    "docs/architecture/data_flow.txt": "DB -> API -> Frontend\n",
    "docs/retrospectives/sprint_42.md": "## Sprint 42\n- Velocity: 34\n- Issues: 3 blockers\n",
    "reports/q1/velocity_report.csv": "sprint,velocity\n41,32\n42,34\n43,29\n",
    "reports/q2/forecast.json": json.dumps({"q2_target": 150, "current": 87}),
    "config/environments/prod.env": "DB_HOST=prod-db.internal\nDB_PORT=5432\n",
    "config/environments/staging.env": "DB_HOST=staging-db.internal\nDB_PORT=5432\n",
    "config/db/schema_v1.sql": "CREATE TABLE old_tasks (id INT, name TEXT);\n",
    "config/db/migration_notes.txt": "Migrated from v1 to v2 on 2024-03-01\n",
    "scripts/migration/run_migration.sh": "#!/bin/bash\necho 'Running migration...'\n",
    "scripts/backup/backup_db.sh": "#!/bin/bash\ncp tasks.db tasks.db.bak\n",
    "src/core/models.py": "# Domain models placeholder\n",
    "src/integrations/slack_notifier.py": "# Slack integration stub\n",
    "tests/unit/test_models.py": "# Unit tests\n",
    "tests/integration/test_api.py": "# Integration tests\n",
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(base, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# ── THE REAL INPUT: sprint_backlog.csv ───────────────────────────────────────
# This CSV contains raw task data that the agent must import and then apply
# business rules to. Columns: title, description, initial_status, initial_priority
backlog_rows = [
    # (title, description, initial_status, initial_priority)
    ("Implement OAuth2 login",       "Add OAuth2 support for SSO",           "pending",     "high"),
    ("Fix payment timeout bug",      "Payments fail after 30s on prod",      "in_progress", "urgent"),
    ("Write API documentation",      "Document all REST endpoints",          "pending",     "low"),
    ("Refactor database layer",      "Extract DB logic into repository",     "pending",     "medium"),
    ("Setup CI/CD pipeline",         "Configure GitHub Actions workflow",    "in_progress", "high"),
    ("Add rate limiting",            "Prevent API abuse with rate limits",   "blocked",     "high"),
    ("Migrate legacy reports",       "Convert old reports to new format",    "pending",     "low"),
    ("Upgrade dependencies",         "Bump all outdated npm packages",       "blocked",     "medium"),
    ("Load testing",                 "Run k6 load tests on staging",         "pending",     "medium"),
    ("Fix CORS headers",             "Resolve CORS errors in frontend",      "completed",   "high"),
    ("Implement audit logging",      "Log all user actions to DB",           "pending",     "high"),
    ("Data retention policy",        "Auto-delete records older than 7y",   "pending",     "low"),
    ("Security penetration test",    "Hire external team for pentest",       "blocked",     "urgent"),
    ("Deploy to EU region",          "Spin up EU datacenter nodes",          "in_progress", "urgent"),
    ("Onboard new dev team member",  "Setup access and dev environment",     "pending",     "medium"),
]

csv_path = os.path.join(base, "sprint_backlog.csv")
with open(csv_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["title", "description", "initial_status", "initial_priority"])
    for row in backlog_rows:
        writer.writerow(row)

# ── Business rules document (plain text, no hints about CLI) ─────────────────
rules_content = """\
SPRINT CLEANUP RULES — Q2 Planning Session
===========================================

Source data: sprint_backlog.csv

Step 1 — Import
  Load every row from sprint_backlog.csv into the task management system,
  preserving the original status and priority of each task.

Step 2 — Escalate blocked urgent tasks
  Any task that is currently BLOCKED and has URGENT priority must be
  escalated: change its priority to remain urgent but flip its status
  to IN_PROGRESS (someone has volunteered to unblock it).

Step 3 — Archive low-priority pending tasks
  Any task that is PENDING with LOW priority is deprioritised for this
  sprint. Mark it as COMPLETED (archived for later review).

Step 4 — Produce final summary
  Write a file called task_summary.json to the workspace root containing:
    {
      "total_tasks": <int>,
      "by_status": {
        "pending":     <int>,
        "in_progress": <int>,
        "completed":   <int>,
        "blocked":     <int>
      },
      "by_priority": {
        "low":    <int>,
        "medium": <int>,
        "high":   <int>,
        "urgent": <int>
      }
    }
  Counts must reflect the state of the database AFTER steps 2 and 3.
"""

with open(os.path.join(base, "sprint_cleanup_rules.txt"), "w") as f:
    f.write(rules_content)

print("Workspace generated successfully.")
print(f"sprint_backlog.csv written with {len(backlog_rows)} rows.")