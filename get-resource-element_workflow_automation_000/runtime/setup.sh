#!/bin/bash
set -e

# Ensure the compare script is executable
chmod +x /workspace/scripts/compare_elements.py

echo "Setup complete. Workspace structure:"
find /workspace -type f | sort