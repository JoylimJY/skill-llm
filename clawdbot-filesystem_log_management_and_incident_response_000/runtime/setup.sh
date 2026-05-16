#!/bin/bash
set -e

# Make the filesystem CLI executable
chmod +x /workspace/.clawdbot/skills/filesystem/filesystem
chmod +x /workspace/bin/filesystem

# Symlink to PATH
ln -sf /workspace/.clawdbot/skills/filesystem/filesystem /usr/local/bin/filesystem

# Verify node is available
node --version

# Smoke test the CLI
filesystem analyze --path /workspace/logs --stats 2>&1 | head -5 || true

echo "Setup complete. 'filesystem' CLI is available in PATH."