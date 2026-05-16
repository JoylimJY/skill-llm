#!/bin/bash
set -e

# Ensure workspace permissions
chmod -R 755 /workspace

echo "Workspace setup complete."
echo "Contents of /workspace:"
ls -la /workspace/