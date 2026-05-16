#!/bin/bash
set -e

# Start the mock Feishu server in the background
cd /workspace
python mock_feishu_server.py &
SERVER_PID=$!
echo "Mock Feishu server started with PID $SERVER_PID"

# Wait for server to be ready
for i in $(seq 1 15); do
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:7777/feishu_search_user \
        -X POST -H "Content-Type: application/json" -d '{"query":"test"}' | grep -q "200"; then
        echo "Server is ready."
        break
    fi
    echo "Waiting for server... ($i)"
    sleep 1
done

# Make server PID available
echo $SERVER_PID > /workspace/.server_pid
chmod +x /workspace/mock_feishu_server.py