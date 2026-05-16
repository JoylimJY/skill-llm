#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace/

echo "Verifying resume file exists..."
if [ -f "/workspace/hr_system/candidates/2025/pending/liming_resume_raw.txt" ]; then
    echo "Resume file found."
else
    echo "ERROR: Resume file missing!"
    exit 1
fi

if [ -f "/workspace/skills/background-check-list/SKILL.md" ]; then
    echo "SKILL.md found."
else
    echo "ERROR: SKILL.md missing!"
    exit 1
fi

echo "Setup complete."