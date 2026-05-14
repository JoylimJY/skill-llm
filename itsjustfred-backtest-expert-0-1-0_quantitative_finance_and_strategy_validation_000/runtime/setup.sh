#!/usr/bin/env bash
set -e

# Ensure workspace permissions
chmod -R 755 /workspace

echo "Sandbox ready. Workspace structure:"
find /workspace -type f | sort