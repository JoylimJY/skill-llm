#!/bin/bash
set -e

echo "=== Setting up MCP Hello World skill environment ==="

# Find where mcp-hello-world was installed globally
MCP_GLOBAL_PATH=$(npm root -g)/mcp-hello-world

echo "MCP Hello World global path: $MCP_GLOBAL_PATH"

# Create a local skill directory in workspace that the agent can use
mkdir -p /workspace/mcp-skill
cd /workspace/mcp-skill

# Copy from global install or install fresh locally
if [ -d "$MCP_GLOBAL_PATH" ]; then
    cp -r $MCP_GLOBAL_PATH/* .
    echo "Copied from global install"
else
    npm install mcp-hello-world --registry https://registry.npmmirror.com || \
    npm install mcp-hello-world
    echo "Installed locally"
fi

# Install dependencies if needed
if [ ! -f "package.json" ]; then
    echo "ERROR: mcp-hello-world not properly installed"
    exit 1
fi

npm install --registry https://registry.npmmirror.com 2>/dev/null || npm install

echo "=== mcp-hello-world skill ready at /workspace/mcp-skill ==="

# Verify mcporter is available
which mcporter && echo "mcporter is available" || echo "WARNING: mcporter not found in PATH"

# Quick smoke test
echo "=== Verifying mcporter can reach server ==="
cd /workspace/mcp-skill
timeout 10 mcporter list --stdio "npm start" 2>/dev/null && echo "Server responds OK" || echo "Server test skipped (will be tested by agent)"

echo "=== Setup complete ==="