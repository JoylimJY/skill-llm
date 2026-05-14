#!/bin/bash
set -e

WORKSPACE="${WORKSPACE:-/workspace}"

# Ensure scripts are executable
chmod +x "$WORKSPACE/scripts/clawhavoc-scan.sh"
chmod +x "$WORKSPACE/scripts/audit-log.sh"
chmod +x "$WORKSPACE/scripts/policy-guard.sh"

# Verify jq is available
jq --version > /dev/null 2>&1 && echo "jq OK" || echo "WARNING: jq not found"

echo "Setup complete. Workspace ready at $WORKSPACE"