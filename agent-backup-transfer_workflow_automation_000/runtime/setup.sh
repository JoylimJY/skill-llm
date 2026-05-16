#!/bin/bash
set -e

echo "[setup] Making backup script executable..."
chmod +x "$HOME/.openclaw/workspace/skills/openclaw-backup/openclaw-backup.sh"

echo "[setup] Verifying pre-existing backup count..."
BACKUP_COUNT=$(ls -1 "$HOME/openclaw-backups"/openclaw-backup-*.tar.gz 2>/dev/null | wc -l)
echo "[setup] Found $BACKUP_COUNT pre-existing backups."

echo "[setup] Workspace contents:"
find "$HOME/.openclaw/workspace" -maxdepth 3 -not -path '*/node_modules/*' -not -path '*/.git/*' | head -40

echo "[setup] Setup complete."