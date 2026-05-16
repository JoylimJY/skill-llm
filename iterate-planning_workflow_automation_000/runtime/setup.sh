#!/bin/bash
set -e

# Initialize git repo in the project directory so Phase 3 commits work
cd /workspace/iot-monitor
git init
git config user.email "agent@benchmark.local"
git config user.name "Agent Under Test"
git add -A
git commit -m "chore: initial codebase snapshot"

echo "Git repo initialized in /workspace/iot-monitor"
echo "Workspace ready."