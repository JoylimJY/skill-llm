#!/bin/bash
set -e

# No background servers needed for this file-generation task.
# Just ensure workspace permissions are correct.
chmod -R 755 /workspace

echo "Setup complete. Workspace is ready."
echo ""
echo "Project structure:"
find /workspace -type f | sort