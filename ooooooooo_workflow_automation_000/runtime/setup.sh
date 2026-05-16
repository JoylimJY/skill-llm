#!/bin/bash
set -e

cd /workspace

# Ensure git is configured
git config user.email "agent@test.local" || true
git config user.name "Agent" || true

# Make scripts executable
find /workspace/scripts -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true

# Initial commit of the distractor/plan files so git baseline exists
git add -A 2>/dev/null || true
git commit -m "Initial workspace setup" 2>/dev/null || true

echo "Setup complete. Workspace ready."