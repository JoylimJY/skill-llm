#!/usr/bin/env bash
set -euo pipefail

# Ensure correct ownership of all home-dir files
chown -R devops:devops /home/devops

# Configure git for devops user
su devops -c "git config --global user.email 'devops@example.com'"
su devops -c "git config --global user.name 'DevOps Agent'"
su devops -c "git config --global init.defaultBranch main"

# Ensure openclaw CLI is executable
chmod +x /usr/local/bin/openclaw

# Ensure backup.sh and restore.sh are executable (belt-and-suspenders)
chmod +x /home/devops/.openclaw/skills/openclaw-backup-restore/scripts/backup.sh
chmod +x /home/devops/.openclaw/skills/openclaw-backup-restore/scripts/restore.sh

echo "Setup complete."