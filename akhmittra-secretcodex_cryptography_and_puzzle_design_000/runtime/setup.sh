#!/bin/bash
set -e

echo "[SETUP] Initializing SecretCodex cipher challenge workspace..."

# Make the reference file unreadable by name (agent won't know to look for it)
chmod 600 /workspace/.eval_reference.json

# Verify workspace structure
echo "[SETUP] Workspace structure:"
tree /workspace --noreport -a 2>/dev/null | head -40 || find /workspace -type f | sort

echo "[SETUP] Mission brief preview:"
head -20 /workspace/puzzles/escape_rooms/series_a/mission_brief.txt

echo "[SETUP] Setup complete. Agent may begin."