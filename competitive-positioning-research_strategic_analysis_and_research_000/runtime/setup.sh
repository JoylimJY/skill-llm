#!/bin/bash
set -e

echo "Setting up CloudLens workspace..."

# Ensure workspace permissions are correct
chmod -R 755 /workspace

# Confirm structure
echo "Workspace ready. Key files:"
ls /workspace/projects/cloudlens/context/
ls /workspace/projects/cloudlens/reviews/

echo "Setup complete."