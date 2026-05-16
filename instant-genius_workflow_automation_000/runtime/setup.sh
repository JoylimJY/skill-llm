#!/usr/bin/env bash
set -euo pipefail

# Make setup.sh executable
chmod +x /workspace/skills/instant-genius/scripts/setup.sh

# Verify the skill structure is in place
echo "[setup] Skill files:"
find /workspace/skills/instant-genius -type f | sort

echo "[setup] Pre-existing AGENTS.md:"
cat ~/.openclaw/workspace/AGENTS.md

echo "[setup] Environment ready. Agent may now proceed."