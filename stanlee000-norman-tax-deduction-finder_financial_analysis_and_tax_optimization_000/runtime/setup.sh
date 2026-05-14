#!/bin/bash
set -e

chmod +x /workspace/tools/scripts/mock_server.py

# Start mock MCP server in background
cd /workspace
python /workspace/tools/scripts/mock_server.py &
MOCK_PID=$!
echo "Mock server started with PID $MOCK_PID"

# Wait for server to be ready
echo "Waiting for mock server to be ready..."
for i in $(seq 1 20); do
    if curl -s http://localhost:7821/health > /dev/null 2>&1; then
        echo "Mock server is ready on port 7821."
        break
    fi
    sleep 0.5
done

# Write server info for agent to discover
cat > /workspace/tools/config/server_info.json << 'EOF'
{
  "mock_server_url": "http://localhost:7821",
  "endpoints": {
    "search_transactions": "POST /search_transactions",
    "get_company_details": "GET /get_company_details",
    "list_tax_settings": "GET /list_tax_settings",
    "categorize_transaction": "POST /categorize_transaction"
  },
  "note": "This is the local norman-finance MCP mock server for development."
}
EOF

echo "Setup complete."