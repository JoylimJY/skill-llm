#!/usr/bin/env bash
set -e

# Ensure workspace is the CWD for the agent
cd /workspace

# Make conversation files readable
chmod 644 /workspace/conversations/*.txt

# Confirm garden CLI is available
which garden && echo "garden CLI found: OK" || echo "WARNING: garden CLI not found"

echo "Setup complete. Workspace ready at /workspace"