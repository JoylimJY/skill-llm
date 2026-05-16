#!/bin/bash
set -e

# Make the tuner script executable
chmod +x /workspace/scripts/oejts_tuner.py

# Verify Python can find the script
python3 /workspace/scripts/oejts_tuner.py --help > /dev/null 2>&1 || true

echo "Setup complete. Workspace ready."