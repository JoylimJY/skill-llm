#!/bin/bash
set -e

# Run the input generation script to populate workspace files
cd /workspace
python3 /workspace/gen_inputs.py

# Make the analysis script executable
chmod +x /workspace/workspace/scripts/analyze_msq.py

# Ensure python3 is accessible from scripts directory
echo "Setup complete. Workspace ready."
echo "Files in workspace:"
find /workspace -type f | sort