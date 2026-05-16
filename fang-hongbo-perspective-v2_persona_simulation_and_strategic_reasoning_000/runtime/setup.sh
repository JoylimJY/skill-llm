#!/bin/bash
set -e

echo "Setting up advisory platform workspace..."

# Ensure SKILL.md is accessible at the standard location
# (In real eval, SKILL.md would be placed here by the harness)
# Make all files readable
chmod -R 644 /workspace/advisory_platform/ 2>/dev/null || true
find /workspace -type d -exec chmod 755 {} \; 2>/dev/null || true

echo "Workspace setup complete."
echo "Workspace contents:"
find /workspace -type f | sort