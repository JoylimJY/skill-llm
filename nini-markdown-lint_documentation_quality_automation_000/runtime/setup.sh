#!/usr/bin/env bash
set -euo pipefail

echo "=== Setting up workspace ==="

# Make the check-horizontal-rules.sh script executable (it already exists per gen_inputs)
chmod +x /workspace/scripts/check-horizontal-rules.sh

# Initialize a git repo so pre-commit can work
cd /workspace
git config --global user.email "ci@medflow.example.com"
git config --global user.name "CI Bot"
git config --global init.defaultBranch main
git init
git add -A
git commit -m "initial messy docs" --no-verify

echo "=== Setup complete ==="
echo "Workspace contents:"
find /workspace -not -path '*/node_modules/*' -not -path '*/.git/*' -type f | sort