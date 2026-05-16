#!/usr/bin/env bash
set -e

echo "=== Setting up nb CLI evaluation environment ==="

# Configure git globally
git config --global user.email "agent@test.local"
git config --global user.name "Agent Test"
git config --global init.defaultBranch main

# Verify nb is installed and functional
if ! command -v nb &>/dev/null; then
    echo "ERROR: nb CLI not found. Attempting install..."
    curl -fsSL https://raw.githubusercontent.com/xwmx/nb/master/nb -o /usr/local/bin/nb
    chmod +x /usr/local/bin/nb
fi

echo "nb version: $(nb --version 2>/dev/null || echo 'unknown')"

# Initialize nb with a default notebook to ensure ~/.nb exists
nb init 2>/dev/null || true

echo "=== Setup complete ==="
echo "Workspace is ready at /workspace"
echo "Task specification: /workspace/task_specification.txt"