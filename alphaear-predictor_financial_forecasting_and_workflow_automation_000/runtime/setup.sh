#!/usr/bin/env bash
set -euo pipefail

# Make all scripts executable
find /workspace/scripts -name "*.py" -exec chmod +x {} \;

# Ensure exports/models directory exists (SKILL.md requirement)
mkdir -p /workspace/exports/models

# Ensure PYTHONPATH includes workspace root so imports work
export PYTHONPATH="/workspace:${PYTHONPATH:-}"
echo "PYTHONPATH set to $PYTHONPATH"

echo "Setup complete."