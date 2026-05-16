#!/usr/bin/env bash
set -e

WORKSPACE="${WORKSPACE:-/workspace}"
cd "$WORKSPACE"

# Initialize a git repo in the workspace so bd can operate
git init -b main
git add .
git commit -m "Initial project scaffold"

echo "Git repo initialized in $WORKSPACE"
echo "bd version: $(bd --version 2>/dev/null || echo 'unknown')"