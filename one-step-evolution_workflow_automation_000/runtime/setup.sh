#!/bin/bash
set -e

echo "=== Setup: Fire Dragon Fruit Architecture Benchmark ==="

# Ensure workspace permissions
chmod -R 755 /workspace

# Confirm the messy state is in place
echo "--- Current workspace state ---"
find /workspace -type f | sort

echo "=== Setup complete. Agent may begin. ==="