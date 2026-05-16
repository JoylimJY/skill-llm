#!/bin/bash
set -euo pipefail

WORKSPACE="${1:-/workspace}"

echo "=== Setting up mock remote bare repository ==="

# Create a bare repository that acts as the remote "origin"
BARE_REPO="/tmp/mock_remote_origin.git"
git init --bare "$BARE_REPO"
echo "Bare remote repository created at: $BARE_REPO"

# Store the bare repo path in a well-known location so the eval can find it
echo "$BARE_REPO" > /tmp/mock_remote_path.txt

# Configure global git to allow local file:// pushes (needed in newer git)
git config --global protocol.file.allow always
git config --global init.defaultBranch main

# Ensure the workspace git repo is sane
cd "$WORKSPACE"
git config --local protocol.file.allow always

echo "=== Setup complete ==="
echo "Agent must:"
echo "  1. Configure git user.name and user.email locally"
echo "  2. Add origin remote pointing to $BARE_REPO"
echo "  3. Run: bash ./scripts/sync.sh"