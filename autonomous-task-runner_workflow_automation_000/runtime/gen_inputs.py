import os
import json
import random
from pathlib import Path
from datetime import datetime, timezone, timedelta

random.seed(42)

workspace = Path("/workspace")

# ── Distractor directory structure ──────────────────────────────────────────
dirs = [
    "projects/infra-team/terraform",
    "projects/infra-team/ansible",
    "projects/app-team/deployments",
    "projects/app-team/configs",
    "logs/2026-01",
    "logs/2026-02",
    "scripts/maintenance",
    "scripts/monitoring",
    "docs/runbooks",
    "docs/architecture",
    ".config/shell",
    "tmp/scratch",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────
distractor_files = {
    "projects/infra-team/terraform/main.tf": '# Terraform main config\nresource "aws_instance" "web" { ami = "ami-0c55b159cbfafe1f0" }',
    "projects/infra-team/terraform/variables.tf": 'variable "region" { default = "us-east-1" }',
    "projects/infra-team/ansible/inventory.ini": "[webservers]\n10.0.0.1\n10.0.0.2",
    "projects/app-team/deployments/k8s-deploy.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: myapp",
    "projects/app-team/configs/app.env": "DATABASE_URL=postgres://localhost/mydb\nREDIS_URL=redis://localhost:6379",
    "logs/2026-01/deploy-log-2026-01-15.txt": "2026-01-15 09:00:00 Deploy started\n2026-01-15 09:05:00 Deploy complete",
    "logs/2026-02/deploy-log-2026-02-03.txt": "2026-02-03 14:00:00 Rollback initiated\n2026-02-03 14:02:00 Rollback complete",
    "scripts/maintenance/cleanup.sh": "#!/bin/bash\nfind /tmp -mtime +7 -delete",
    "scripts/monitoring/health-check.py": "import requests\nresp = requests.get('http://localhost:8080/health')\nprint(resp.status_code)",
    "docs/runbooks/incident-response.md": "# Incident Response\n1. Page on-call\n2. Check dashboards\n3. Identify root cause",
    "docs/architecture/system-overview.md": "# System Overview\nOur platform consists of 3 microservices...",
    ".config/shell/aliases.sh": "alias ll='ls -la'\nalias gs='git status'",
    "tmp/scratch/notes.txt": "TODO: fix the broken pipeline\ncheck memory leak in service B",
}
for path, content in distractor_files.items():
    (workspace / path).write_text(content)

# ── Misleading / partial task-related files (distractors) ───────────────────
# A fake old queue file in the WRONG location to mislead the agent
wrong_queue_dir = workspace / "tmp" / "old-tasks"
wrong_queue_dir.mkdir(parents=True, exist_ok=True)
(wrong_queue_dir / "task-queue.json").write_text(json.dumps({
    "note": "DEPRECATED - do not use",
    "tasks": []
}, indent=2))

# A partial HEARTBEAT.md with unrelated entries (no Task Runner entry yet)
heartbeat_content = """# Heartbeat Configuration

## System Health Check
Every heartbeat: ping internal services
- Check /health endpoints
- If any DOWN → alert on-call

## Log Rotation
Every heartbeat: check log sizes
- If logs > 500MB → compress and archive
"""
(workspace / "HEARTBEAT.md").write_text(heartbeat_content)

# ── Pre-seeded task-queue.json in the CORRECT location ──────────────────────
# This simulates a partially-initialized queue from a previous session
# The agent must READ this, respect existing lastId="T-02", and extend from it.
# T-01 is "done", T-02 is "running" (agent will be told to skip it via control command)
tasks_dir = Path.home() / ".openclaw" / "tasks"
tasks_dir.mkdir(parents=True, exist_ok=True)

pre_seeded_queue = {
    "version": "1.0",
    "maxConcurrent": 2,
    "maxRetries": 3,
    "archiveDays": 7,
    "taskRunnerDir": "~/.openclaw/tasks/",
    "lastId": "T-02",
    "tasks": [
        {
            "id": "T-01",
            "description": "check if the staging database is reachable",
            "goal": "Verify network connectivity to the staging PostgreSQL database at db-staging.internal:5432",
            "type": "code-execution",
            "status": "done",
            "retries": 0,
            "maxRetries": 3,
            "subagent_session": "agent:main:subagent:aaa111",
            "strategies_tried": [
                {
                    "attempt": 1,
                    "strategy": "exec",
                    "tool": "exec",
                    "attempted_at": "2026-03-10T08:00:00Z",
                    "result": "nc -zv db-staging.internal 5432 returned exit 0",
                    "verification_failure": None
                }
            ],
            "deliverable": "Staging DB reachable at db-staging.internal:5432",
            "deliverable_path": None,
            "blocked_reason": None,
            "user_action_required": None,
            "added_at": "2026-03-10T07:55:00Z",
            "started_at": "2026-03-10T08:00:00Z",
            "completed_at": "2026-03-10T08:03:00Z"
        },
        {
            "id": "T-02",
            "description": "restart the nginx service on web-prod-01",
            "goal": "Restart the nginx web server service on the production host web-prod-01",
            "type": "code-execution",
            "status": "running",
            "retries": 1,
            "maxRetries": 3,
            "subagent_session": "agent:main:subagent:bbb222",
            "strategies_tried": [
                {
                    "attempt": 1,
                    "strategy": "exec",
                    "tool": "exec",
                    "attempted_at": "2026-03-10T08:05:00Z",
                    "result": "SSH connection timed out",
                    "verification_failure": None
                }
            ],
            "deliverable": None,
            "deliverable_path": None,
            "blocked_reason": None,
            "user_action_required": None,
            "added_at": "2026-03-10T07:55:00Z",
            "started_at": "2026-03-10T08:05:00Z",
            "completed_at": None
        }
    ]
}

queue_file = tasks_dir / "task-queue.json"
queue_file.write_text(json.dumps(pre_seeded_queue, indent=2))

# ── TOOLS.md with Task Runner config ────────────────────────────────────────
tools_content = """# Tools Configuration

## Task Runner
TASK_RUNNER_DIR=~/.openclaw/tasks/
TASK_RUNNER_MAX_CONCURRENT=2
TASK_RUNNER_MAX_RETRIES=3
TASK_RUNNER_ARCHIVE_DAYS=7

## General
WORKSPACE=/workspace
"""
(workspace / "TOOLS.md").write_text(tools_content)

# ── Additional distractor: a fake tasks directory in /workspace ──────────────
fake_tasks_dir = workspace / "tasks"
fake_tasks_dir.mkdir(exist_ok=True)
(fake_tasks_dir / "README.txt").write_text("This is NOT the task runner directory. See TOOLS.md.")
(fake_tasks_dir / "old-format-tasks.csv").write_text("id,description,status\n1,deploy app,done\n2,check logs,pending")

print("Workspace initialized successfully.")
print(f"Queue file pre-seeded at: {queue_file}")
print(f"HEARTBEAT.md created at: {workspace / 'HEARTBEAT.md'}")