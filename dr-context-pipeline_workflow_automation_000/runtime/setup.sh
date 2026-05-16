#!/usr/bin/env bash
set -e

# Make all pipeline scripts executable
chmod +x /workspace/skills/dr-context-pipeline/scripts/*.py

# Ensure git config is set for any git operations the agent runs
git -C /workspace config user.email "agent@benchmark.local" 2>/dev/null || true
git -C /workspace config user.name "Agent" 2>/dev/null || true

# Verify the workspace looks correct
echo "=== Workspace root ==="
ls -1 /workspace

echo "=== Memory structure ==="
ls -1 /workspace/memory/topics/

echo "=== Pipeline scripts ==="
ls -1 /workspace/skills/dr-context-pipeline/scripts/

echo "=== Schemas available ==="
ls -1 /workspace/skills/dr-context-pipeline/references/schemas/

echo "Setup complete."