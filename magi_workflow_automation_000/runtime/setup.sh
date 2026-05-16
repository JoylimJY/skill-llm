#!/bin/bash
set -e

# Ensure the skills/magi directory is writable
chmod -R 755 /workspace/skills/magi/

# Make SKILL.md read-only (as per spec: "SKILL.md is read-only to the agent")
chmod 444 /workspace/skills/magi/SKILL.md

echo "Setup complete. skills/magi/ is ready."
echo "SKILL.md permissions: $(stat -c '%a' /workspace/skills/magi/SKILL.md)"