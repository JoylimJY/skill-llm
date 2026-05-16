#!/usr/bin/env bash
set -e

# Make the shared-context script executable
chmod +x ~/.openclaw/workspace/scripts/shared-context.py

# Verify the structure
echo "[setup] Workspace structure:"
find ~/.openclaw/workspace -type f | sort

echo "[setup] Pre-existing shared data:"
cat ~/.openclaw/workspace/shared/highlights.json || echo "(empty)"
cat ~/.openclaw/workspace/shared/trends.json || echo "(empty)"

echo "[setup] Ready."