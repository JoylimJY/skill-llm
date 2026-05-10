#!/usr/bin/env bash
set -euo pipefail

echo "--- Setting up skill environment ---"
cd /workspace/skill_context

# Install npm dependencies if not already done
if [ ! -d "node_modules" ]; then
    npm install 2>/dev/null || echo "npm install attempted"
fi

# Make scripts executable
chmod +x /workspace/tools/scripts/deploy.sh 2>/dev/null || true

echo "--- Skill context ready ---"
ls -la /workspace/skill_context/
echo "--- Setup complete ---"