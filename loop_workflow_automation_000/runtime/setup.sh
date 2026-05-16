#!/bin/bash
set -e

# Ensure the scoring script is executable
chmod +x /workspace/biolab/scripts/run_scoring.sh

# Ensure HOME loop directory does NOT pre-exist (agent must create it per skill spec)
rm -rf ~/loop

echo "Setup complete. ~/loop does not exist yet — agent must create it."
echo "Scoring script is at /workspace/biolab/scripts/run_scoring.sh (always exits 1)"