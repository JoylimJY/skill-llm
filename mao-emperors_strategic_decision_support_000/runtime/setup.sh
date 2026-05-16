#!/bin/bash
set -e

# Ensure workspace directory exists
mkdir -p /workspace

# Copy SKILL.md to workspace so the agent can read it
if [ -f "/SKILL.md" ]; then
    cp /SKILL.md /workspace/SKILL.md
    echo "SKILL.md copied to workspace"
fi

# Make workspace readable/writable
chmod -R 755 /workspace

echo "Setup complete. Workspace ready at /workspace"
ls /workspace/