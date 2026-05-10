#!/usr/bin/env bash
set -euo pipefail

echo "=== Setting up skill dependencies ==="
cd /workspace/skill_context

# Install npm dependencies for the skill
if [ -f "package.json" ]; then
    npm install --prefer-offline 2>/dev/null || npm install
    echo "npm dependencies installed."
fi

# Ensure reports directory exists
mkdir -p /workspace/reports

echo "=== Setup complete ==="