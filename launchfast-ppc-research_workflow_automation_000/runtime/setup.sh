#!/usr/bin/env bash
set -e

# Make the mock server executable
chmod +x /workspace/tools/mcp_server.py

# Start the mock MCP server in background
cd /workspace/tools
python3 mcp_server.py &
MCP_PID=$!
echo "Mock MCP server started with PID $MCP_PID"

# Wait for it to be ready
for i in $(seq 1 15); do
    if curl -s http://localhost:7771/health > /dev/null 2>&1; then
        echo "MCP server is ready."
        break
    fi
    sleep 1
done

# Ensure Downloads directory exists
mkdir -p /root/Downloads

echo "Setup complete."