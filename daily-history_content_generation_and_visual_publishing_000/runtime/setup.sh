#!/bin/bash
set -e

# Ensure output directory exists
mkdir -p /mnt/user-data/outputs

# Make push-toggle script executable
chmod +x /workspace/scripts/push-toggle.js 2>/dev/null || true

# Ensure workspace permissions
chmod -R 755 /workspace

echo "[setup] Environment ready."
echo "[setup] Output directory: /mnt/user-data/outputs"
echo "[setup] Workspace: /workspace"