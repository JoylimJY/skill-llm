#!/bin/bash
set -e

chmod +x /workspace/scripts/leadership-prompts.js

# Verify Node.js is available
node --version

# Verify the CLI works with existing prompts
echo "Verifying CLI setup..."
node /workspace/scripts/leadership-prompts.js list
echo "Setup complete."