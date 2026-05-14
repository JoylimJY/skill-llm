#!/bin/bash
set -e

# Ensure workspace ownership is correct
chown -R devuser:devuser /home/devuser/workspace 2>/dev/null || true

# Ensure the home directory for devuser credential path exists
mkdir -p /home/devuser/.leetcode-mcp
chown -R devuser:devuser /home/devuser/.leetcode-mcp

echo "Setup complete."
echo "Workspace: /home/devuser/workspace"
echo "Credential dir ready: /home/devuser/.leetcode-mcp"