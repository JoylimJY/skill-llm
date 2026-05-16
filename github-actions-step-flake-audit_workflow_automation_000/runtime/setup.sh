#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${WORKSPACE:-/workspace}"

# Ensure scripts are executable
chmod +x "$WORKSPACE/skills/github-actions-step-flake-audit/scripts/step-flake-audit.sh"  || true
chmod +x "$WORKSPACE/skills/github-actions-step-flake-audit/scripts/step-flake-audit.py"  || true

echo "Setup complete. Workspace at: $WORKSPACE"
ls -lh "$WORKSPACE/artifacts/github-actions/" | head -30