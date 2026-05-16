#!/bin/bash
set -e

# Ensure workspace permissions are correct
chmod -R 755 /workspace

# Verify the raw conversation files exist
echo "Verifying workspace setup..."
ls /workspace/raw_conversations/
ls /workspace/memory/

echo "Setup complete. Workspace is ready for agent."