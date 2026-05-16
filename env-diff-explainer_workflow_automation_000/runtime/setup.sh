#!/usr/bin/env bash
set -e

SKILL_DIR="${WORKSPACE_DIR:-/workspace}/skills/env-diff-explainer"

# Make the run.py executable
chmod +x "$SKILL_DIR/scripts/run.py"

# Verify the skill structure is intact
echo "[setup] Skill directory contents:"
find "$SKILL_DIR" -type f | sort

echo "[setup] Config files:"
find "${WORKSPACE_DIR:-/workspace}/ecommerce-platform/configs/release-q4" -type f | sort

echo "[setup] Setup complete."