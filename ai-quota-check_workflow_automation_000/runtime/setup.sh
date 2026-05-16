#!/usr/bin/env bash
set -euo pipefail

# Make the mock skill executable
chmod +x /workspace/skills/ai-quota-check/index.js

# Verify Node.js is available
node --version

# Smoke-test the mock script runs without error
echo "--- Smoke test: full dashboard ---"
node /workspace/skills/ai-quota-check/index.js

echo "--- Smoke test: coding task ---"
node /workspace/skills/ai-quota-check/index.js --task=coding

echo "--- Smoke test: reasoning task ---"
node /workspace/skills/ai-quota-check/index.js --task=reasoning

echo ""
echo "Setup complete. Workspace is ready."