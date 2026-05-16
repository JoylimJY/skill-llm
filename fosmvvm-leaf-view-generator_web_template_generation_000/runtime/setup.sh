#!/usr/bin/env bash
set -e

echo "=== TaskFlow sandbox ready ==="
echo "Workspace structure:"
find /workspace -type f | sort
echo ""
echo "The agent must create the two Leaf template files."