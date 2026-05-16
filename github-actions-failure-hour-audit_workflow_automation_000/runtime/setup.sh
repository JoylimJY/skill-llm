#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${WORKSPACE:-/workspace}"

chmod +x "$WORKSPACE/skills/github-actions-failure-hour-audit/scripts/failure-hour-audit.sh"

echo "[setup] Workspace ready. Script is executable."
ls -lh "$WORKSPACE/skills/github-actions-failure-hour-audit/scripts/"