#!/usr/bin/env bash
set -e

# Initialize git repo so the agent can commit the design doc as the skill requires
cd /workspace
git config --global user.email "agent@sandbox.local"
git config --global user.name "Agent Sandbox"
git init -b main
git add -A
git commit -m "chore: initial project scaffold"

echo "Setup complete. Git repo initialized at /workspace"
echo "Workspace contents:"
find /workspace -type f | sort