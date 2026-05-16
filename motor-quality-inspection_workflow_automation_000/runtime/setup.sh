#!/bin/bash
set -e

# Make the inspection report script executable
chmod +x /workspace/scripts/inspection_report.py

# Verify the script works
cd /workspace
python scripts/inspection_report.py --list

echo "Setup complete. Workspace ready."