#!/bin/bash
set -e

# Ensure workspace permissions are correct
chmod -R 755 /workspace

# Create a timestamped marker so the eval script can verify WAL happened before other writes
# We record the setup completion time; the agent's SESSION-STATE.md must be created during its work
SETUP_DONE_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
echo "SETUP_COMPLETE_AT=${SETUP_DONE_TIME}" > /workspace/.setup_marker

echo "Setup complete at ${SETUP_DONE_TIME}"
echo "Workspace ready for agent task."