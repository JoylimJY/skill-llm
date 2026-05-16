#!/bin/bash
set -e

# Ensure workspace permissions
chmod -R 755 /workspace

# Confirm submissions exist
echo "=== Submission files ==="
ls /workspace/submissions/*.json 2>/dev/null || echo "No submission JSON files found"

echo "=== Workspace structure ==="
find /workspace -type f | sort

echo "Setup complete."