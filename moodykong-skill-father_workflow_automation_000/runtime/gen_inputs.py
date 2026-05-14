import os
import random
import stat

random.seed(42)

WORKSPACE = os.environ.get("WORKSPACE", "/workspace")

# Create a realistic, deeply nested directory structure to simulate an existing skills monorepo
dirs = [
    "skills/ssh-op",
    "skills/ssh-op/scripts",
    "skills/ssh-op/references",
    "skills/docker-manager",
    "skills/docker-manager/scripts",
    "skills/git-sync",
    "skills/git-sync/scripts",
    "skills/git-sync/references",
    "tools/bin",
    "tools/lib",
    "config/global",
    "docs/internal",
    "docs/architecture",
    ".local/bin",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# Distractor files - existing skills with correct layout (to show what good looks like, but NOT for the new skill)
distractor_files = {
    "skills/ssh-op/SKILL.md": """---
name: skill-ssh-op
description: Manages SSH keys via 1Password.
---
# SSH-OP Skill

## Prerequisites
- `op whoami` must succeed
- `ssh`, `ssh-add`, `ssh-agent` must exist: `command -v ssh`

## Configuration
Config lives in this skill folder.
- `config.env.example` — shareable example (never modified by onboarding)
- `config.env` — real machine-specific values (written by onboarding)

Required keys:
- `OP_VAULT` — 1Password vault name
- `SSH_KEY_ITEM` — item name in vault

## Initialization / Onboarding

### Preferred (chat-first)
1. Agent asks: which vault? which SSH key item?
2. Agent writes `config.env`.
3. Agent runs `scripts/smoke-test.sh` and reports.

### Optional (terminal)
Run `scripts/onboard.sh` in a real terminal.

## Reproducibility
All config is parameterized. No hardcoded paths.
""",
    "skills/ssh-op/config.env.example": 'OP_VAULT="my-vault"\nSSH_KEY_ITEM="my-ssh-key"\n',
    "skills/ssh-op/config.env": 'OP_VAULT="personal"\nSSH_KEY_ITEM="laptop-key"\n',
    "skills/ssh-op/scripts/onboard.sh": "#!/bin/bash\necho 'Onboarding ssh-op...'\n",
    "skills/ssh-op/scripts/smoke-test.sh": "#!/bin/bash\nop whoami && echo 'OK'\n",
    "skills/docker-manager/SKILL.md": "---\nname: skill-docker-manager\ndescription: Manages Docker containers.\n---\n# Docker Manager\n## Prerequisites\n- `command -v docker` must succeed\n",
    "skills/docker-manager/scripts/run.sh": "#!/bin/bash\ndocker ps\n",
    "skills/git-sync/SKILL.md": "---\nname: skill-git-sync\ndescription: Syncs git repos.\n---\n# Git Sync\n## Prerequisites\n- `command -v git`\n",
    "skills/git-sync/references/git-notes.md": "Advanced git notes go here.\n",
    "tools/bin/openclaw": "#!/bin/bash\necho 'openclaw v1.0'\n",
    "tools/lib/utils.sh": "#!/bin/bash\necho 'utils'\n",
    "config/global/settings.json": '{"theme": "dark", "lang": "en"}\n',
    "docs/internal/onboarding-guide.md": "Welcome to DataVault Corp. See skills/ for automation.\n",
    "docs/architecture/system-overview.md": "DataVault Corp uses OpenClaw for skill-based automation.\n",
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(WORKSPACE, rel_path)
    with open(full_path, "w") as f:
        f.write(content)
    if rel_path.endswith(".sh"):
        os.chmod(full_path, os.stat(full_path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

# Create the task brief: a raw, informal notes file describing what the new skill should do
# This is the "messy input" the agent must interpret
task_brief_content = """\
DATAVAULT CORP — INTERNAL TASK BRIEF
=====================================
New skill request: db-backup

Purpose:
  Automate nightly PostgreSQL database backups to S3-compatible storage.
  Team members on different machines need to be able to use this.

Required configuration (machine-specific, varies per user/machine):
  - DB_HOST: hostname of the postgres server (e.g. localhost or db.internal)
  - DB_PORT: port number (default 5432)
  - DB_USER: postgres username
  - DB_NAME: name of the database to back up
  - S3_BUCKET: target bucket name
  - S3_ENDPOINT: S3-compatible endpoint URL
  - BACKUP_RETENTION_DAYS: how many days to keep backups (default 7)

External tools required:
  - pg_dump (from postgresql-client package)
  - aws CLI (s3 operations)
  - Any credential management tool the team uses

The backup script itself (scripts/run-backup.sh) is already written and lives
in the skill folder — do NOT recreate it.

There are also some extended docs about S3 lifecycle policies and pg_dump flags
that should be accessible but not clutter the main skill file.

The skill should be runnable by a new team member on a fresh machine with 
minimal friction. Consider that some team members primarily use a chat interface
to interact with the automation system.

Contact: ops-team@datavault.corp
"""

with open(os.path.join(WORKSPACE, "db-backup-task-brief.txt"), "w") as f:
    f.write(task_brief_content)

# Pre-create the scripts/run-backup.sh (the brief says it already exists)
os.makedirs(os.path.join(WORKSPACE, "skills/db-backup/scripts"), exist_ok=True)
backup_script = """\
#!/bin/bash
# DataVault Corp - db-backup run script
# Loads config from ../config.env
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../config.env"
echo "Backing up $DB_NAME from $DB_HOST:$DB_PORT..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="/tmp/${DB_NAME}_${TIMESTAMP}.dump"
pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -Fc "$DB_NAME" -f "$BACKUP_FILE"
aws --endpoint-url "$S3_ENDPOINT" s3 cp "$BACKUP_FILE" "s3://${S3_BUCKET}/backups/"
echo "Backup complete: $BACKUP_FILE"
"""
backup_script_path = os.path.join(WORKSPACE, "skills/db-backup/scripts/run-backup.sh")
with open(backup_script_path, "w") as f:
    f.write(backup_script)
os.chmod(backup_script_path, os.stat(backup_script_path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

# Also pre-create an onboarding script stub (the brief implies one should exist)
onboard_script = """\
#!/bin/bash
# db-backup onboarding script (Optional - terminal use)
# Run this in a real terminal for interactive setup.
set -euo pipefail
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_FILE="$SKILL_DIR/config.env"
EXAMPLE_FILE="$SKILL_DIR/config.env.example"

echo "=== db-backup Onboarding ==="
echo "This will generate $CONFIG_FILE"

prompt_with_default() {
    local key="$1"
    local default="$2"
    local current=""
    if [ -f "$CONFIG_FILE" ]; then
        current=$(grep "^${key}=" "$CONFIG_FILE" 2>/dev/null | cut -d= -f2- | tr -d '"' || true)
    fi
    local show="${current:-$default}"
    read -rp "$key [$show]: " val
    echo "${val:-$show}"
}

DB_HOST=$(prompt_with_default DB_HOST "localhost")
DB_PORT=$(prompt_with_default DB_PORT "5432")
DB_USER=$(prompt_with_default DB_USER "postgres")
DB_NAME=$(prompt_with_default DB_NAME "mydb")
S3_BUCKET=$(prompt_with_default S3_BUCKET "my-backup-bucket")
S3_ENDPOINT=$(prompt_with_default S3_ENDPOINT "https://s3.amazonaws.com")
BACKUP_RETENTION_DAYS=$(prompt_with_default BACKUP_RETENTION_DAYS "7")

cat > "$CONFIG_FILE" <<EOF
DB_HOST="$DB_HOST"
DB_PORT="$DB_PORT"
DB_USER="$DB_USER"
DB_NAME="$DB_NAME"
S3_BUCKET="$S3_BUCKET"
S3_ENDPOINT="$S3_ENDPOINT"
BACKUP_RETENTION_DAYS="$BACKUP_RETENTION_DAYS"
EOF

echo "Config written to $CONFIG_FILE"
echo "Run scripts/smoke-test.sh to validate."
"""
onboard_script_path = os.path.join(WORKSPACE, "skills/db-backup/scripts/onboard.sh")
with open(onboard_script_path, "w") as f:
    f.write(onboard_script)
os.chmod(onboard_script_path, os.stat(onboard_script_path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

print("Workspace initialized successfully.")
print(f"Workspace root: {WORKSPACE}")