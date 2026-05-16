#!/bin/bash
set -e

echo "=== Setting up Japanese Daily Drill evaluation environment ==="

# Make sure workspace exists
mkdir -p /workspace

# Verify SKILL.md is present
if [ -f /workspace/SKILL.md ]; then
    echo "[OK] SKILL.md found"
else
    echo "[ERROR] SKILL.md missing!"
    exit 1
fi

# Set permissions
chmod -R 755 /workspace

echo "=== Setup complete ==="
echo "Agent task: Read SKILL.md and generate drill_session.md for N3 level"