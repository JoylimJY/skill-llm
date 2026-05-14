import os
import random
import textwrap

random.seed(42)

workspace = "/workspace"

# ── Distractor structure ──────────────────────────────────────────────────────
dirs = [
    "platform/agents/deployments",
    "platform/agents/configs",
    "platform/monitoring/dashboards",
    "platform/monitoring/alerts",
    "legacy/old-skills/db-helper",
    "legacy/old-skills/file-watcher",
    "docs/runbooks",
    "docs/onboarding",
    "tmp/scratch",
    "tmp/logs",
    "infra/terraform/modules",
    "infra/ansible/playbooks",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), f=True)

# Distractor files
distractor_files = {
    "platform/agents/configs/agent_config.yaml": "model: gpt-4\nmax_tokens: 4096\ntemperature: 0.2\n",
    "platform/agents/deployments/deploy.sh": "#!/bin/bash\nkubectl apply -f deployment.yaml\n",
    "platform/monitoring/dashboards/overview.json": '{"panels": [], "title": "Agent Overview"}\n',
    "platform/monitoring/alerts/cpu_alert.yaml": "alert: HighCPU\nexpr: cpu > 80\n",
    "legacy/old-skills/db-helper/notes.txt": "old backup script - DEPRECATED do not use\n",
    "legacy/old-skills/file-watcher/SKILL.md": textwrap.dedent("""\
        ---
        name: file-watcher
        description: Watches filesystem for changes
        ---
        # File Watcher
        Monitors directories.
        """),
    "docs/runbooks/incident_response.md": "# Incident Response\n1. Page on-call\n2. Assess severity\n",
    "docs/onboarding/getting_started.md": "# Getting Started\nWelcome to the platform.\n",
    "tmp/scratch/test_query.sql": "SELECT * FROM backups WHERE status='failed';",
    "tmp/logs/agent_run_20240101.log": "[INFO] Agent started\n[INFO] Skill loaded: file-watcher\n[ERROR] Connection timeout\n",
    "infra/terraform/modules/rds.tf": 'resource "aws_db_instance" "main" { allocated_storage = 100 }\n',
    "infra/ansible/playbooks/postgres_setup.yml": "- name: Install postgres\n  apt:\n    name: postgresql\n",
}

for path, content in distractor_files.items():
    full = os.path.join(workspace, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)

# ── THE PROBLEM: messy raw notes from a colleague ────────────────────────────
# These are rough notes about a PostgreSQL backup skill.
# They have the right ideas but are unstructured, violate naming/format rules,
# and contain detail that should go into references/, not inline.

raw_notes_content = textwrap.dedent("""\
    ROUGH NOTES - PostgreSQL Backup Automation
    ==========================================
    Written by: Jordan (DevOps)
    Date: Some time last quarter

    What this does:
    Automates nightly PostgreSQL database backups, uploads to object storage,
    rotates old backups (keep last 30 days), sends alert on failure.
    Use this skill when you need to back up postgres databases, schedule db backups,
    rotate old database snapshots, or handle pg_dump automation.

    This is CRITICAL infrastructure - it runs every night and if it breaks,
    we lose backup coverage. No room for improvisation here, must be exact.

    Steps the agent should do:
    1. Run pg_dump with these exact flags:
       pg_dump -Fc -Z 9 -h $DB_HOST -U $DB_USER -d $DB_NAME -f /backups/$DB_NAME_$(date +%Y%m%d).dump
    2. Upload to object storage:
       aws s3 cp /backups/$DB_NAME_$(date +%Y%m%d).dump s3://$BACKUP_BUCKET/postgres/$DB_NAME/
    3. Rotate: delete files in /backups/ older than 30 days:
       find /backups/ -name "*.dump" -mtime +30 -delete
    4. On failure, run: ./scripts/alert_oncall.sh "backup failed: $DB_NAME"

    Parameters needed:
    - DB_HOST (required)
    - DB_USER (required)  
    - DB_NAME (required)
    - BACKUP_BUCKET (required)

    Detailed technical appendix:
    =============================
    pg_dump format flags:
    -Fc = custom format (compressed, supports parallel restore)
    -Z 9 = max compression level
    Restore command: pg_restore -Fc -d target_db backup_file.dump
    
    S3 bucket policy requirements:
    The backup bucket must have versioning enabled. IAM role needs:
    s3:PutObject, s3:GetObject, s3:DeleteObject, s3:ListBucket
    Lifecycle rules should be set to expire objects after 90 days as safety net.
    
    Rotation logic detail:
    We keep 30 days local, 90 days in S3. The find command uses mtime not ctime.
    Edge case: if disk is >90% full, run emergency rotation keeping only 7 days.
    
    Error handling detail:
    alert_oncall.sh calls PagerDuty API with severity=critical
    Also writes to /var/log/backup_errors.log
    Retry logic: attempt backup 3 times with 5 min sleep between attempts
    
    Historical context:
    We switched from mysqldump in 2019. Had an incident in 2021 where backups
    silently failed for 2 weeks. That's why we added the alerting.
    
    IMPORTANT NAMING NOTE:
    If this becomes a skill, name it something like "PostgreSQL DB Backup Skill"
    or "pg backup" or "Postgres_Backup_V2" -- Jordan wasn't sure about naming conventions.
    
    This is about 200 lines of detail total in these notes which is fine for a doc,
    but might be too much for an agent skill file I guess? Not sure.
""")

notes_path = os.path.join(workspace, "tmp/scratch/jordan_backup_notes.txt")
with open(notes_path, "w") as f:
    f.write(raw_notes_content)

# Also drop a secondary file with additional chaff
extra_notes = textwrap.dedent("""\
    misc todos
    - ask platform team about skill naming rules
    - figure out how to structure the scripts folder
    - does the description have a character limit??
    - remember: skill name must match folder name (someone mentioned this)
    - skill file should NOT be enormous - keep it short, move details elsewhere
""")
with open(os.path.join(workspace, "tmp/scratch/misc_todos.txt"), "w") as f:
    f.write(extra_notes)

print("Workspace initialized.")
print("Key input file: tmp/scratch/jordan_backup_notes.txt")