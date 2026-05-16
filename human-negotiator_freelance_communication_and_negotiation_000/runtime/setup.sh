#!/bin/bash
set -e

echo "Setting up workspace..."

# Ensure the workspace is properly set up
chmod -R 755 /workspace

echo "Setup complete. Workspace ready."
echo "The agent should process /workspace/incoming_messages.json"
echo "and produce response_drafts.json"