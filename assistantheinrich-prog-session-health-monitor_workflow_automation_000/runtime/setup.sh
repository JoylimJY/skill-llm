#!/usr/bin/env bash
set -euo pipefail

# Ensure scripts are executable (belt-and-suspenders after gen_inputs_script)
chmod +x /workspace/scripts/context-check.sh
chmod +x /workspace/scripts/snapshot.sh
chmod +x /workspace/scripts/rotate.sh

# Install bc for arithmetic in context-check.sh if not present
which bc || apt-get install -y bc 2>/dev/null || true

# Verify jq is available
jq --version

echo "Setup complete. Workspace ready."
ls -la /workspace/scripts/
ls -la /workspace/memory/