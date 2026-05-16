#!/bin/bash
set -e

SKILL_DIR="$HOME/.openclaw/skills/agent-mbti"

# Make run script executable
chmod +x "$SKILL_DIR/scripts/run-diagnosis.sh"

# Create output directory
mkdir -p "$SKILL_DIR/output"

echo "[setup] Skill directory: $SKILL_DIR"
echo "[setup] Scripts marked executable."
echo "[setup] Output directory ready."
ls -la "$SKILL_DIR/scripts/"
ls -la "$SKILL_DIR/data/"