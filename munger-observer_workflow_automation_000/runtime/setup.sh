#!/bin/bash
set -e

echo "Setting up Munger Observer sandbox..."

# Ensure workspace permissions are correct
chmod -R 755 /workspace

# Confirm target memory file exists
TARGET="memory/2025-06-12.md"
if [ -f "/workspace/$TARGET" ]; then
    echo "✓ Target memory file verified: $TARGET"
else
    echo "✗ ERROR: Target memory file missing!"
    exit 1
fi

echo "Sandbox ready. Workspace contains $(find /workspace -type f | wc -l) files."