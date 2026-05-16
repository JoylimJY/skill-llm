#!/bin/bash
set -e

# Make scripts executable
chmod +x /workspace/mood-diary/scripts/journal.py
chmod +x /workspace/mood-diary/scripts/mood-report.py

# Ensure the openclaw data directory exists
mkdir -p ~/.openclaw/workspace/data/journal

# Verify the skill is accessible
echo "=== Mood Diary Skill Check ==="
python3 /workspace/mood-diary/scripts/journal.py moods
echo "=== Setup Complete ==="