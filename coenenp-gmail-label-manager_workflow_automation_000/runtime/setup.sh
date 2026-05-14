#!/bin/bash
set -euo pipefail

WORKSPACE="${WORKSPACE_DIR:-/workspace}"

# Ensure gog mock is executable
chmod +x /usr/local/bin/gog

# Ensure script.sh is executable
chmod +x "${WORKSPACE}/script.sh"

# Ensure log directory exists and is writable
mkdir -p "${WORKSPACE}/logs"
chmod 777 "${WORKSPACE}/logs"

# Clear any prior gog call log to ensure clean evaluation
rm -f "${WORKSPACE}/logs/gog_calls.log"

echo "Setup complete. Mock gog CLI is ready."
echo "Workspace: ${WORKSPACE}"
echo "script.sh: $(ls -la ${WORKSPACE}/script.sh)"