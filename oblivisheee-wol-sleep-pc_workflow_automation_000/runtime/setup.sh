#!/usr/bin/env bash
set -e

chmod +x /workspace/scripts/send_wol.py
chmod +x /workspace/scripts/send_sleep.py

# Clear any stale log files from previous runs
rm -f /tmp/wol_invocations.log
rm -f /tmp/sol_invocations.log

echo "Setup complete. Scripts are executable."