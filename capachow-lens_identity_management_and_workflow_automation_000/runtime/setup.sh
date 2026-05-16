#!/usr/bin/env bash
set -e

# Make lens scripts executable
chmod +x /workspace/skills/lens/scripts/bootstrap.js 2>/dev/null || true
chmod +x /workspace/skills/lens/scripts/distillation.js 2>/dev/null || true

# Confirm .lens does NOT exist at task start
if [ -d "/workspace/.lens" ]; then
  rm -rf /workspace/.lens
  echo "[setup] Removed stale .lens directory"
fi

echo "[setup] Workspace ready. .lens/ does not exist — Onboarding Protocol required."