#!/usr/bin/env bash
set -e

# Ensure all proposal directories are writable
chmod -R 755 /workspace/proposals
chmod -R 755 /workspace/meeting-notes
chmod -R 755 /workspace/assets

echo "Setup complete. Workspace ready at /workspace."