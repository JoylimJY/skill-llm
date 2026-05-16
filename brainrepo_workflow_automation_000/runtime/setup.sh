#!/bin/bash
set -e

# Ensure git is configured for the root user
git config --global user.email "agent@test.local"
git config --global user.name "Agent Test"
git config --global init.defaultBranch main

# Make sure the Documents directory exists and is writable
mkdir -p /root/Documents

echo "Setup complete. Workspace ready at /workspace"
echo "Brain dump file location: /workspace/todays-brain-dump.txt"
ls /workspace/