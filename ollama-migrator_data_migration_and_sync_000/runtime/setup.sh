#!/usr/bin/env bash
set -e

chmod +x /workspace/scripts/check_ollama_status.py
chmod +x /workspace/scripts/migrate_ollama.py
chmod +x /workspace/scripts/verify_ollama.py

# Ensure logs dir is writable
mkdir -p /workspace/logs

echo "[setup] Workspace initialized."
echo "[setup] Primary storage:"
find /workspace/primary_storage -type f | head -20
echo "[setup] Scripts available:"
ls -la /workspace/scripts/