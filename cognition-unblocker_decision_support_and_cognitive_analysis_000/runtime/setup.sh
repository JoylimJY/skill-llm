#!/bin/bash
set -e

# Ensure workspace permissions are correct
chmod -R 755 /workspace

# Verify the scenario file is present
if [ ! -f /workspace/user_scenario.txt ]; then
    echo "ERROR: user_scenario.txt not found!"
    exit 1
fi

echo "Setup complete. Workspace ready."
echo "Key input file: /workspace/user_scenario.txt"
echo "Expected output file: /workspace/decision_analysis.md"