#!/bin/bash
set -e

echo "=== Setting up Feynman Coach sandbox ==="

# Ensure all necessary directories exist and have correct permissions
mkdir -p /workspace/.opencode
mkdir -p /workspace/Z_Utils/feynman-coach/history
mkdir -p /workspace/skills/feynman-coach

chmod -R 755 /workspace

echo "=== Workspace structure ==="
find /workspace -type f | sort

echo "=== Setup complete ==="