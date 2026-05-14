#!/bin/bash
set -e

echo "[setup] Workspace ready. No additional runtime services needed."

# Make maintenance scripts executable (realistic environment detail)
chmod +x /workspace/scripts/maintenance/clear_sessions.sh
chmod +x /workspace/scripts/maintenance/restart_gateway.sh

# Simulate ~/.openclaw being the workspace config location
# The agent should edit workspace/.openclaw/openclaw.json
echo "[setup] Setup complete."
ls -la /workspace/.openclaw/