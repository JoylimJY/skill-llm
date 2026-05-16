#!/bin/bash
set -e

# Ensure workspace permissions are correct
chmod -R 755 /workspace

# Verify SKILL.md is accessible
if [ -f "/workspace/SKILL.md" ]; then
    echo "[setup] SKILL.md found at /workspace/SKILL.md"
else
    echo "[setup] WARNING: SKILL.md not found at /workspace/SKILL.md"
fi

echo "[setup] Environment ready."