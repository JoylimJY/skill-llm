#!/bin/bash
set -e

# Create workspace directory
mkdir -p /workspace
cp -r /app/* /workspace/ 2>/dev/null || true
cd /workspace

# Set up environment variable for anthropic (will be empty in eval)
export ANTHROPIC_API_KEY="sk-test-key-for-development"

echo "Setup complete. Workspace ready at /workspace"