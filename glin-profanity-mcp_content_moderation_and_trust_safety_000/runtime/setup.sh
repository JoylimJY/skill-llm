#!/bin/bash
set -e

echo "=== Setting up sandbox environment ==="

# Ensure npm global bin is in PATH
export PATH="$(npm bin -g 2>/dev/null || npm root -g | sed 's/node_modules$/bin/'):$PATH"

# Pre-warm the glin-profanity-mcp package cache so agent doesn't hit cold-start timeouts
echo "Pre-warming glin-profanity-mcp..."
timeout 30 npx -y glin-profanity-mcp 2>/dev/null &
WARMUP_PID=$!
sleep 5
kill $WARMUP_PID 2>/dev/null || true

# Install the core glin-profanity library for direct Node usage as well
cd /workspace
npm init -y > /dev/null 2>&1 || true
npm install glin-profanity glin-profanity-mcp 2>/dev/null || true

# Create a small MCP JSON-RPC helper the agent can reference or use
cat > /workspace/mcp_helper.md << 'EOF'
# MCP Server JSON-RPC Usage

To call an MCP tool programmatically, start the server and exchange JSON-RPC messages over stdin/stdout.

## Initialize
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"cli","version":"1.0"}}}

## List tools
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}

## Call a tool
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"TOOL_NAME","arguments":{...}}}
EOF

echo "=== Setup complete ==="
echo "Workspace files:"
find /workspace/moderation -type f