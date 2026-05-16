#!/bin/bash
set -e

echo "=== Setting up workspace runtime environment ==="

# Ensure git is configured inside the container
git config --global user.email "agent@devteam.local"
git config --global user.name "Developer Agent"
git config --global init.defaultBranch main

# Install node dependencies using pnpm so `pnpm build` works
cd /workspace
pnpm install --registry https://registry.npmmirror.com 2>/dev/null || true

echo "=== Workspace ready ==="
echo "Current branch: $(git -C /workspace branch --show-current)"
echo "Available branches: $(git -C /workspace branch -a)"