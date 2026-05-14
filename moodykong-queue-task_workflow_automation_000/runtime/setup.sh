#!/usr/bin/env bash
set -e

# Ensure the queue_task script is executable
chmod +x /workspace/scripts/queue_task.py

# Verify Python is accessible
python3 --version

echo "[setup] Workspace ready."
echo "[setup] Task slug to recover: compound-screen-2024"
echo "[setup] config.env.example is at /workspace/config.env.example"