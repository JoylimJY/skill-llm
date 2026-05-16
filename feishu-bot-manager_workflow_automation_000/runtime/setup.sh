#!/bin/bash
set -euo pipefail

WORKSPACE="${1:-/workspace}"

# Make all scripts executable
chmod +x "$WORKSPACE/scripts/feishu-bot.sh"
chmod +x "$WORKSPACE/scripts/openclaw"
chmod +x "$WORKSPACE/tools/monitoring/check_bots.sh"
chmod +x "$WORKSPACE/tools/deploy/deploy.sh"

# Add scripts directory to PATH so 'openclaw' is callable as a system command
export PATH="$WORKSPACE/scripts:$PATH"
echo "export PATH=\"$WORKSPACE/scripts:\$PATH\"" >> /etc/bash.bashrc
echo "export PATH=\"$WORKSPACE/scripts:\$PATH\"" >> /root/.bashrc

# Ensure log directory is writable
mkdir -p "$WORKSPACE/logs/gateway"
chmod 755 "$WORKSPACE/logs/gateway"

echo "Setup complete. Workspace: $WORKSPACE"
echo "PATH updated to include $WORKSPACE/scripts"