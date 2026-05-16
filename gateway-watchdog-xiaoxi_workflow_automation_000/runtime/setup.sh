#!/bin/bash
set -e

# Ensure scripts are executable
chmod +x /workspace/gateway_watchdog.py
chmod +x /workspace/install.py
chmod +x /usr/local/bin/openclaw

# Clean any leftover state from previous runs
rm -f /tmp/gateway_watchdog_state.json
rm -f /tmp/gateway_watchdog.log

echo "Setup complete. Workspace ready."
echo "State files cleared."
ls -la /workspace/