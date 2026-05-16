#!/usr/bin/env bash
set -euo pipefail

# Ensure HOME is set to the workspace so the backup script targets the right location.
# The agent will operate with HOME pointing at the workspace directory.
WORKSPACE="${1:-/root/workspace}"

export HOME="${WORKSPACE}"

# Make the backup script executable (idempotent)
chmod +x "${WORKSPACE}/scripts/openclaw-backup.sh"

echo "[setup] HOME set to: ${HOME}"
echo "[setup] .openclaw contents:"
ls -la "${WORKSPACE}/.openclaw/"

echo "[setup] Ready."