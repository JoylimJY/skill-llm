#!/bin/bash
set -e

echo "[setup] Setting permissions on backup.js..."
chmod +x /root/.openclaw/workspace/skills/openclaw-backup/scripts/backup.js

echo "[setup] Installing npm dependencies for openclaw-backup skill..."
cd /root/.openclaw/workspace/skills/openclaw-backup
npm install --registry https://registry.npmmirror.com 2>&1 | tail -5

echo "[setup] Verifying node and script..."
node --version
node scripts/backup.js --help || true

echo "[setup] Listing pre-created old backups..."
ls -la /root/backups/openclaw/ || echo "(empty)"

echo "[setup] Done."