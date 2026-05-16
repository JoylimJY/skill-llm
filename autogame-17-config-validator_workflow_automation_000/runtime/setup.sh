#!/usr/bin/env bash
set -e

# Make the validator executable
chmod +x /workspace/skills/config-validator/index.js

# Ensure node is available and record version for debugging
node --version
npm --version

echo "Setup complete. Workspace is ready for agent."