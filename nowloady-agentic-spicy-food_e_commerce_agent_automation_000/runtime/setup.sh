#!/bin/bash
set -e

echo "=== Setting up Lafeitu mock environment ==="

# Ensure state directory exists and is clean
rm -rf /tmp/lafeitu_mock_state
mkdir -p /tmp/lafeitu_mock_state

# Make scripts executable
chmod +x /workspace/scripts/lafeitu_client.py
chmod +x /workspace/scripts/mock_server.py

# Start mock server in background
echo "Starting mock API server on port 8999..."
python3 /workspace/scripts/mock_server.py > /tmp/mock_server.log 2>&1 &
MOCK_PID=$!
echo "Mock server PID: $MOCK_PID"

# Wait for server to be ready
for i in $(seq 1 20); do
    if curl -s http://127.0.0.1:8999/api/v1/promotions > /dev/null 2>&1; then
        echo "Mock server is ready."
        break
    fi
    sleep 0.5
done

# Verify server is responding
if ! curl -s http://127.0.0.1:8999/api/v1/promotions > /dev/null 2>&1; then
    echo "ERROR: Mock server failed to start. Check /tmp/mock_server.log"
    cat /tmp/mock_server.log
    exit 1
fi

# Point the client to the local mock server
export LAFEITU_API_URL="http://127.0.0.1:8999/api/v1"
echo "export LAFEITU_API_URL=http://127.0.0.1:8999/api/v1" >> /etc/environment
echo "export LAFEITU_API_URL=http://127.0.0.1:8999/api/v1" >> /root/.bashrc
echo "export LAFEITU_API_URL=http://127.0.0.1:8999/api/v1" >> /root/.profile

# Ensure credentials directory exists
mkdir -p /root/.openclaw/credentials/agent-commerce-engine/lafeitu.cn/

echo "=== Setup complete ==="
echo "API URL: http://127.0.0.1:8999/api/v1"
echo "Workspace: /workspace"