#!/bin/bash
set -e

# Ensure workspace permissions
chmod -R 755 /workspace

# Initialize a git repo in the workspace so the agent can commit before deleting
cd /workspace
git config --global user.email "agent@test.local"
git config --global user.name "TestAgent"
git init
git add -A
git commit -m "Initial messy prototype — iteration 7"

echo "Setup complete. Git repo initialized with initial commit."
echo "Workspace ready at /workspace"