#!/bin/bash
set -e

# Ensure workspace permissions are correct
chmod -R 755 /workspace

# Create the output directory where the agent should write results
mkdir -p /workspace/reports/final

echo "Setup complete. Workspace ready."