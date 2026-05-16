#!/usr/bin/env bash
set -e

echo "=== Setting up workspace ==="

# Make scripts executable
chmod +x /workspace/scripts/index-memory.py
chmod +x /workspace/scripts/search-memory.py

# Ensure memory/cache dir pre-exists so permissions are clean
mkdir -p /workspace/memory/cache

echo "=== Setup complete ==="
ls -la /workspace/scripts/