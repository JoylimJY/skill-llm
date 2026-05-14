#!/bin/bash
set -e

# Make the main.js executable
chmod +x /workspace/skill/scripts/main.js

# Install npm dependencies (no external deps, but needed for package resolution)
cd /workspace/skill
npm install --prefer-offline 2>/dev/null || npm install

echo "Setup complete. Skill ready at /workspace/skill/scripts/main.js"

# Verify node is available
node --version
echo "Node.js verified."