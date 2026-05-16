#!/bin/bash
set -e

WORKSPACE="/root/.openclaw/workspace"
SCRIPTS_DIR="$WORKSPACE/skills/personality-switcher/scripts"

# Make all scripts executable
chmod +x "$SCRIPTS_DIR"/*.py

# Verify the workspace structure is intact
echo "=== Workspace Structure ==="
ls -la "$WORKSPACE/"
echo ""
echo "=== Personalities ==="
ls -la "$WORKSPACE/personalities/"
echo ""
echo "=== Scripts ==="
ls -la "$SCRIPTS_DIR/"
echo ""
echo "=== Initial State ==="
cat "$WORKSPACE/_personality_state.json"
echo ""
echo "=== Pre-existing Backups ==="
ls -la "$WORKSPACE/personalities/backups/"
echo ""
echo "Setup complete. Workspace ready for agent task."