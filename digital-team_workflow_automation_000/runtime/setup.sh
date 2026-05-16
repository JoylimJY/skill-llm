#!/bin/bash
set -e

echo "=== Setting up digital-team skill evaluation environment ==="

# Ensure workspace directories exist
mkdir -p /workspace/workspace/agents
mkdir -p /workspace/workspace/knowledge

# Make scripts executable if any exist
find /workspace -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true

echo "=== Environment ready ==="
echo "Current workspace structure:"
find /workspace/workspace -type f | sort