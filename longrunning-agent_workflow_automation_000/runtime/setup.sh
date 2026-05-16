#!/bin/bash
set -e

# Ensure git is configured for the workspace user
git config --global user.email "agent@test.local"
git config --global user.name "Agent Test"

# Make init.sh executable in case permissions were lost
chmod +x /workspace/genomics-pipeline/init.sh 2>/dev/null || true

echo "Setup complete. Workspace ready at /workspace/genomics-pipeline"