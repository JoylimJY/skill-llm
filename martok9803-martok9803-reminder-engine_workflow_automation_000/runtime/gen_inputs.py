import os
import json
import random
import time

random.seed(42)

base = "/workspace"

# Create deeply nested distractor directory structure
dirs = [
    "projects/alpha/src/utils",
    "projects/alpha/src/models",
    "projects/alpha/tests",
    "projects/beta/config",
    "projects/beta/deploy/scripts",
    "team/schedules/archived",
    "team/schedules/active",
    "notifications/templates",
    "notifications/history",
    "logs/2024/jan",
    "logs/2024/feb",
    "config/environments",
]

for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# Distractor files
distractors = {
    "projects/alpha/src/utils/date_helper.py": "# date utilities\nimport datetime\ndef now(): return datetime.datetime.now()\n",
    "projects/alpha/src/models/task.py": "class Task:\n    def __init__(self, name, due): self.name=name; self.due=due\n",
    "projects/alpha/tests/test_task.py": "import unittest\nclass TestTask(unittest.TestCase): pass\n",
    "projects/beta/config/settings.json": json.dumps({"env": "production", "timeout": 30, "retries": 3}),
    "projects/beta/deploy/scripts/deploy.sh": "#!/bin/bash\necho 'deploying...'\n",
    "team/schedules/archived/q1_2024.csv": "date,event\n2024-01-15,Sprint kickoff\n2024-02-01,Retrospective\n",
    "team/schedules/active/current_sprint.md": "# Sprint 42\n- Task A\n- Task B\n- Daily standup at 9:00 AM\n",
    "notifications/templates/email_template.html": "<html><body>Hello {name}, you have a notification.</body></html>",
    "notifications/history/sent_2024_feb.log": "2024-02-01 09:00 - standup reminder sent\n2024-02-02 09:00 - standup reminder sent\n",
    "logs/2024/jan/app.log": "2024-01-10 ERROR: Connection timeout\n2024-01-11 INFO: Service restarted\n",
    "logs/2024/feb/app.log": "2024-02-05 INFO: Deployment successful\n2024-02-06 WARN: High memory usage\n",
    "config/environments/production.env": "DB_HOST=db.internal\nDB_PORT=5432\nAPP_PORT=8080\n",
    "config/environments/staging.env": "DB_HOST=db-staging.internal\nDB_PORT=5432\nAPP_PORT=8081\n",
}

for path, content in distractors.items():
    full = os.path.join(base, path)
    with open(full, "w") as f:
        f.write(content)

# Pre-seed the mock cron store with one existing job that needs to be snoozed
# This simulates an already-existing reminder that the agent must find and snooze
existing_jobs = [
    {
        "jobId": "job_abc123",
        "name": "deployment-checklist-review",
        "schedule": {
            "kind": "at",
            "time": "2025-06-15T14:00:00"
        },
        "sessionTarget": "main",
        "payload": {
            "kind": "systemEvent",
            "text": "Reminder: review the deployment checklist before the release."
        },
        "status": "active",
        "nextRun": "2025-06-15T14:00:00"
    },
    {
        "jobId": "job_xyz789",
        "name": "weekly-report",
        "schedule": {
            "kind": "cron",
            "expr": "0 17 * * 5",
            "tz": "America/New_York"
        },
        "sessionTarget": "main",
        "payload": {
            "kind": "systemEvent",
            "text": "Reminder: submit weekly report to manager."
        },
        "status": "active",
        "nextRun": "2025-06-20T17:00:00"
    }
]

# Write the cron store (this is what the mock server uses as its backing store)
cron_store_path = os.path.join(base, ".cron_store.json")
with open(cron_store_path, "w") as f:
    json.dump({"jobs": existing_jobs, "call_log": []}, f, indent=2)

# Write agent context file describing the task scenario
context_path = os.path.join(base, "task_context.md")
with open(context_path, "w") as f:
    f.write("""# Team Lead Reminder Setup

You are helping configure automated reminders for a software engineering team lead.

## Background
- The team is in the America/New_York timezone.
- The team lead runs a daily standup every weekday morning.
- There is already a "deployment checklist review" reminder in the system (job_abc123) 
  that was supposed to fire today but needs to be pushed back by 30 minutes.

## What needs to be done:
1. Set up a recurring weekday reminder at 9:15 AM (America/New_York) to run the team standup.
   Message: "run the team standup"

2. Snooze the existing deployment checklist reminder (job_abc123) by 30 minutes.
   (The original was scheduled for 14:00 - push it to 14:30 same day: 2025-06-15T14:30:00)

## Cron service endpoint: http://localhost:7291
""")

print("Workspace initialized successfully.")
print(f"Cron store created at: {cron_store_path}")
print("Distractor files created.")