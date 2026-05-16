#!/usr/bin/env bash
set -euo pipefail

echo "[setup] Making all memoria scripts executable..."
chmod +x /workspace/memoria-system/memory-migrate.sh
chmod +x /workspace/memoria-system/memory-health-check.sh
chmod +x /workspace/memoria-system/memory-backup.sh
chmod +x /workspace/memoria-system/memory-rollback.sh

echo "[setup] Verifying jq is available..."
jq --version

echo "[setup] Verifying tar is available..."
tar --version | head -1

echo "[setup] Workspace contents:"
find /workspace -maxdepth 3 -not -path '*/\.*' | sort

echo "[setup] Current config.json:"
cat /workspace/memoria-system/config.json

echo "[setup] Current memory structure:"
find /workspace/memoria-system/memory -type f -o -type d 2>/dev/null | sort || echo "(memory dir not fully present)"

echo "[setup] Setup complete."