#!/bin/bash
set -e

# Ensure openclaw is executable
chmod +x /usr/local/bin/openclaw 2>/dev/null || true

# Ensure the skill is executable
chmod +x /skills/markdown-validator/index.js 2>/dev/null || true

# Verify the skill can be invoked
echo "Verifying skill availability..."
openclaw exec node /skills/markdown-validator/index.js --help 2>/dev/null || true
echo "Setup complete. Workspace ready at /workspace"