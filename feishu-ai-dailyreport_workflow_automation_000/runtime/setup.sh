#!/bin/bash
set -e

# Ensure the workspace directory exists
mkdir -p /root/.openclaw/workspace
mkdir -p /workspace

# Set timezone info but don't override Python's timezone handling
# The agent MUST use UTC+8 programmatically
export TZ=UTC

# Create a helper script the agent can inspect (but it's incomplete - just a hint of the structure)
cat > /workspace/README_SYSTEM.txt << 'EOF'
This system manages AI assistant agents.
Agent session data is stored under /root/.openclaw/agents/
Team workspace is at /root/.openclaw/workspace/
EOF

echo "Setup complete. Container timezone: UTC. Agent must use Beijing time (UTC+8) programmatically."