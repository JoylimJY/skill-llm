#!/bin/bash
set -e

# Initialize git repo for the project (needed for /review workflow context)
cd /workspace
git init
git config user.email "agent@test.local"
git config user.name "Agent Test"
git add -A
git commit -m "Initial sprint 14 codebase"

echo "Git repo initialized with initial commit."
echo "Workspace ready for agent task."