#!/usr/bin/env bash
set -euo pipefail

# Ensure the provisioner script is executable
chmod +x /workspace/provisioner/provision.sh

# Ensure legacy distractor scripts are NOT executable (they should not be confused with the real tool)
chmod -x /workspace/scripts/legacy/old_setup.sh 2>/dev/null || true

echo "[setup] Workspace ready."
echo "[setup] Provisioner available at: /workspace/provisioner/provision.sh"