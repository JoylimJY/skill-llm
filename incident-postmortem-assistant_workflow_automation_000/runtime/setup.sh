#!/usr/bin/env bash
set -e

# Ensure run.py is executable
chmod +x /workspace/skills/incident-postmortem-assistant/scripts/run.py

# Verify the skill tree is intact
echo "=== Skill directory tree ==="
find /workspace/skills/incident-postmortem-assistant -type f | sort

echo "=== Task input file ==="
wc -l /workspace/incident_raw_notes.txt

echo "=== Setup complete ==="