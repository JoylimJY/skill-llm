#!/bin/bash
set -e

echo "=== Setup: OKR Work Manager Task Environment ==="

# Make sure workspace dir permissions are correct
chmod -R 755 /workspace/.okr-work-manager/
chmod 644 /workspace/.okr-work-manager/**/*.json 2>/dev/null || true

# Display the workspace structure so agent can orient itself
echo "=== Workspace structure ==="
find /workspace -maxdepth 4 -not -path '*/\.*' | head -50

echo "=== OKR directory contents ==="
find /workspace/.okr-work-manager -type f | sort

echo "=== Raw December notes (agent input) ==="
cat /workspace/docs/meetings/december_2025_raw_notes.txt

echo "=== Current (broken) OKR config ==="
cat /workspace/.okr-work-manager/okr_config.json

echo ""
echo "Setup complete. Agent should now process the Q4 2025 OKR management workflow."