#!/bin/bash
set -e

# Make all shell scripts executable
find /workspace -name "*.sh" -exec chmod +x {} \;

echo "Setup complete. Workspace ready."
echo "Files in workspace:"
find /workspace -type f | sort