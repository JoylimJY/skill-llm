#!/bin/bash
set -e

# Make the diff tool executable
chmod +x /workspace/scripts/diff.py

echo "Setup complete. Diff tool is ready."
echo "Workspace structure:"
find /workspace -type f | sort