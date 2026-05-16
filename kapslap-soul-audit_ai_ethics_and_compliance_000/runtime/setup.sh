#!/bin/bash
set -e

# Ensure workspace permissions are correct
chmod -R 755 /workspace

echo "Setup complete. Workspace ready."
echo "Files in workspace:"
find /workspace -type f | sort