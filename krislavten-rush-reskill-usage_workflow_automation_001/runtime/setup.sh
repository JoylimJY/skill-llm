#!/bin/bash
set -e

# Ensure reskill is available (global install or npx fallback)
if ! which reskill > /dev/null 2>&1; then
    echo "reskill not found globally, installing..."
    npm install -g reskill --registry https://registry.npmjs.org || true
fi

echo "reskill availability check:"
which reskill && reskill --version || echo "reskill not available via PATH, npx will be used"

# Ensure git is configured
git config --global user.email "agent@test.local" 2>/dev/null || true
git config --global user.name "Agent Test" 2>/dev/null || true

# Make workspace writable
chmod -R 777 /workspace

echo "Setup complete. Project directory: /workspace/platform-engineering/ai-workspace"
ls /workspace/platform-engineering/ai-workspace/