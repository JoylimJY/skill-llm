#!/bin/bash
set -e

# Ensure the main script is executable
chmod +x /workspace/scripts/daily_briefing.py

# Ensure output directory is writable
chmod 755 /workspace/output/

echo "Setup complete. Workspace ready."