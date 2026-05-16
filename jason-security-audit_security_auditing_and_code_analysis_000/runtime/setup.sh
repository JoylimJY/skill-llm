#!/usr/bin/env bash
set -e

# Make audit.py executable in both locations
chmod +x /workspace/audit.py
chmod +x /workspace/plugins/algo-signal-processor/audit.py

echo "Setup complete. Workspace ready."
echo "Plugin directory:"
ls -la /workspace/plugins/algo-signal-processor/
echo ""
echo "Workspace root:"
ls /workspace/