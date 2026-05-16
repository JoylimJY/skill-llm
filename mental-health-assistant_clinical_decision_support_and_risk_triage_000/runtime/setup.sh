#!/bin/bash
set -e

# Ensure workspace permissions are correct
chmod -R 755 /workspace

echo "Setup complete. Workspace ready at /workspace"
echo "Pending intake records:"
ls /workspace/intake_system/pending_review/