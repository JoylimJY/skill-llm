#!/usr/bin/env bash
set -e

echo "=== Setting up sandbox environment ==="

# Ensure workspace permissions
chmod -R 755 "${WORKSPACE:-/workspace}"

echo "=== Setup complete ==="
echo "Workspace contents:"
find "${WORKSPACE:-/workspace}" -type f | sort