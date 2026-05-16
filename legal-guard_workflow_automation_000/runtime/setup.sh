#!/usr/bin/env bash
set -e

WORKSPACE="${WORKSPACE:-/workspace}"
echo "[setup] Workspace: $WORKSPACE"

# Ensure all files are readable
find "$WORKSPACE" -type f -exec chmod 644 {} \;
find "$WORKSPACE" -type d -exec chmod 755 {} \;

echo "[setup] Permissions set."
echo "[setup] Setup complete. Agent may begin."