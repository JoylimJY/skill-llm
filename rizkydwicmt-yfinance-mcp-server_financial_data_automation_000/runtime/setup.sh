#!/bin/bash
set -e

# Make tool scripts executable
chmod +x /workspace/tools/mock_server.py
chmod +x /workspace/tools/yf_tool.py

# Start the mock MCP server in background
cd /workspace/tools
nohup python mock_server.py > /workspace/logs/mock_server.log 2>&1 &

# Wait for server to be ready
sleep 2

# Verify server is up
curl -s -X POST http://127.0.0.1:8080/call \
  -H "Content-Type: application/json" \
  -d '{"tool": "tool_screen_stocks", "params": {"sector": "Healthcare"}}' \
  > /dev/null && echo "Mock server ready." || echo "WARNING: Mock server may not be ready."

echo "Setup complete. Tool client at /workspace/tools/yf_tool.py"
echo "Example usage:"
echo "  python /workspace/tools/yf_tool.py tool_screen_stocks sector=Healthcare min_market_cap=10000000000 max_pe_ratio=25 min_dividend_yield=0.02"