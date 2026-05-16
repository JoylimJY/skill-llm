#!/bin/bash
set -e

# Initialize git in the project directory
cd /workspace/projects/drone-fw/collision-avoidance
git config --global user.email "agent@test.local"
git config --global user.name "Agent Test"
git init
git add -A
git commit -m "Initial project state"

echo "Setup complete. Project git-initialized."
echo "Workspace tree:"
tree /workspace --dirsfirst -a 2>/dev/null | head -80 || find /workspace -type f | sort | head -80