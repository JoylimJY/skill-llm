#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Verifying key files exist..."
if [ ! -f "/workspace/sessions/active/session_active_20240315.json" ]; then
    echo "ERROR: session input file missing!"
    exit 1
fi

if [ ! -f "/workspace/skills/nantong-local-life/SKILL.md" ]; then
    echo "ERROR: SKILL.md missing!"
    exit 1
fi

echo "Setup complete. Workspace ready."
ls -la /workspace/sessions/active/
ls -la /workspace/skills/nantong-local-life/