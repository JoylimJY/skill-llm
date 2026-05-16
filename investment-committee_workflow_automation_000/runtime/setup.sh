#!/bin/bash
set -e

WORKSPACE="${WORKSPACE:-/workspace}"

chmod +x "${WORKSPACE}/investment-committee/scripts/fetch_price.py"
chmod +x "${WORKSPACE}/investment-committee/scripts/old_fetch_v1.py"

# Ensure history directory is writable
mkdir -p "${WORKSPACE}/investment-committee/history"
chmod 755 "${WORKSPACE}/investment-committee/history"

echo "Setup complete. Workspace: ${WORKSPACE}"