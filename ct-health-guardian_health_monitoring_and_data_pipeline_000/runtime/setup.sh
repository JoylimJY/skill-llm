#!/bin/bash
set -e

chmod +x /workspace/scripts/import_health.py
chmod +x /workspace/scripts/analyze.py
chmod +x /workspace/scripts/summary.py

echo "Setup complete. Workspace ready."
echo "Current workspace structure:"
find /workspace -type f | sort