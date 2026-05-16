#!/bin/bash
set -e

# Ensure git is configured for the session
git config --global user.email "agent@test.local"
git config --global user.name "Agent Test"
git config --global init.defaultBranch main

# Make scripts executable
chmod +x /workspace/payflow-lib/scripts/release.sh

echo "[SETUP] Environment ready. Workspace: /workspace/payflow-lib"
echo "[SETUP] Current branch:"
git -C /workspace/payflow-lib branch

echo "[SETUP] All branches:"
git -C /workspace/payflow-lib branch -a

echo "[SETUP] Log graph:"
git -C /workspace/payflow-lib log --graph --oneline --all