#!/bin/bash
set -e

# Start the mock API server in the background
echo "[setup] Starting mock sessions API server on port 7878..."
python /workspace/mock_server.py &
MOCK_PID=$!
echo $MOCK_PID > /workspace/mock_server.pid

# Wait for server to be ready
for i in $(seq 1 15); do
    if curl -s http://localhost:7878/sessions_list > /dev/null 2>&1; then
        echo "[setup] Mock server is ready."
        break
    fi
    echo "[setup] Waiting for mock server... ($i/15)"
    sleep 1
done

# Verify the server is actually running
if ! curl -s http://localhost:7878/sessions_list > /dev/null 2>&1; then
    echo "[setup] ERROR: Mock server failed to start."
    exit 1
fi

# Create mock_server_logs dir (server also creates it, but ensure permissions)
mkdir -p /workspace/mock_server_logs

echo "[setup] Environment ready. Mock server PID: $MOCK_PID"
echo "[setup] Available endpoints:"
echo "  GET/POST http://localhost:7878/sessions_list"
echo "  POST     http://localhost:7878/sessions_send"
echo "  POST     http://localhost:7878/sessions_spawn"