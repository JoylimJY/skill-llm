#!/bin/bash
set -e

# Ensure workspace permissions
chmod -R 755 /workspace

# Create the memory directory if it somehow doesn't exist
mkdir -p /workspace/memory

echo "Setup complete. Workspace ready."
ls /workspace/