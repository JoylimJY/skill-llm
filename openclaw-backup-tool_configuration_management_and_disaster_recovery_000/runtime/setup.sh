#!/bin/bash
set -e

# Make all OpenClaw scripts executable
chmod +x ~/.openclaw/workspace/skills/openclaw-backup/scripts/backup.sh
chmod +x ~/.openclaw/workspace/skills/openclaw-backup/scripts/restore.sh
chmod +x ~/.openclaw/workspace/skills/openclaw-backup/scripts/restart.sh

# Make workspace scripts executable
chmod +x /workspace/scripts/health_check.sh 2>/dev/null || true
chmod +x /workspace/scripts/deploy.sh 2>/dev/null || true
chmod +x /workspace/scripts/migrate_db.sh 2>/dev/null || true

echo "[setup] OpenClaw backup environment ready."
echo "[setup] Scripts available at: ~/.openclaw/workspace/skills/openclaw-backup/scripts/"
echo "[setup] Active config: ~/.openclaw/openclaw.json"