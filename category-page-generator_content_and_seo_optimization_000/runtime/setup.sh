#!/bin/bash
set -e

# Ensure workspace permissions are correct
chmod -R 755 /workspace

echo "Sandbox ready. Workspace contents:"
find /workspace -type f | sort