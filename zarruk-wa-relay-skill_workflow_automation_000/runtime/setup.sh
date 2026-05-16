#!/usr/bin/env bash
set -euo pipefail

# Ensure scripts are executable
chmod +x /workspace/scripts/setup.sh
chmod +x /workspace/scripts/configure.sh

echo "[setup_script] Workspace ready."
echo "[setup_script] Scripts:"
ls -la /workspace/scripts/