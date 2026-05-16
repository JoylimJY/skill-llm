#!/bin/bash
set -e

# Make the skill script executable
chmod +x /workspace/scripts/script.sh 2>/dev/null || true

# Ensure CONSOLIDATION_DIR exists (default per SKILL.md)
mkdir -p ~/.consolidation/

# Verify the script is actually runnable
if [ -f /workspace/scripts/script.sh ]; then
    echo "[setup] scripts/script.sh found and made executable."
else
    echo "[setup] WARNING: scripts/script.sh not found. Agent must locate it."
fi

echo "[setup] Setup complete."