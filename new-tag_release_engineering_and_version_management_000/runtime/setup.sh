#!/usr/bin/env bash
set -e

cd /workspace

# Make scripts executable
chmod +x scripts/check-versions.sh scripts/clean.sh

# Configure git to allow the workspace directory (safe.directory)
git config --global safe.directory /workspace
git config --global user.email "dev@acme.io"
git config --global user.name "ACME Dev"

# Confirm git remote is reachable
echo "Remote refs:"
git ls-remote origin || echo "(remote check skipped)"

echo "Setup complete."