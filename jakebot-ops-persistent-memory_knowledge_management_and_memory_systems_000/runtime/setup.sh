#!/usr/bin/env bash
set -e

echo "=== Runtime Setup ==="

# Ensure the workspace ownership is correct
chown -R root:root /workspace 2>/dev/null || true

# Make the skill scripts executable
chmod +x /workspace/skills/persistent-memory/scripts/unified_setup.sh
chmod +x /workspace/skills/persistent-memory/scripts/configure_openclaw.py

echo "=== Runtime Setup Complete ==="