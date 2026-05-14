#!/bin/bash
set -e

echo "=== Setting up workspace ==="

# Make deploy scripts executable (distractor files)
chmod +x /workspace/scripts/deploy/deploy.sh 2>/dev/null || true
chmod +x /workspace/scripts/migrate/run_migrations.sh 2>/dev/null || true

# Ensure docs/decisions directory does NOT pre-exist (agent must handle creating it or the skill creates it)
# The SKILL.md says to create the directory if needed — the agent must handle this
rm -rf /workspace/docs/decisions

echo "=== Setup complete ==="
echo "Workspace structure:"
tree /workspace --dirsfirst -L 3 2>/dev/null || find /workspace -type f | head -30