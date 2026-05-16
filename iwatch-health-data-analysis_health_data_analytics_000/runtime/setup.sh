#!/bin/bash
set -e

chmod +x /workspace/scripts/parse_health.py
chmod +x /workspace/scripts/generate_report.py

# Ensure /tmp is writable
chmod 1777 /tmp

echo "[setup] Scripts marked executable."
echo "[setup] Workspace contents:"
find /workspace -type f | sort