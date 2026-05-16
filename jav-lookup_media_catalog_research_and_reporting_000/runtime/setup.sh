#!/bin/bash
set -e

chmod +x /workspace/tools/scripts/mock_javdb_server.py 2>/dev/null || true
chmod +x /workspace/tools/scripts/batch_query_old.sh 2>/dev/null || true

# Start the mock JAVDB server in background
python3 /workspace/tools/scripts/mock_javdb_server.py &
MOCK_PID=$!
echo $MOCK_PID > /tmp/mock_server.pid
echo "Mock JAVDB server started with PID $MOCK_PID on port 7788"

# Wait for server to be ready
for i in $(seq 1 15); do
    if curl -s http://localhost:7788/health > /dev/null 2>&1; then
        echo "Mock server is ready."
        break
    fi
    echo "Waiting for mock server... ($i/15)"
    sleep 1
done

# Verify it's actually up
curl -s http://localhost:7788/health && echo "Mock server health check passed."

echo "Setup complete. Mock JAVDB available at http://localhost:7788"
echo "Search endpoint: http://localhost:7788/search?q=<CODE>&f=all"
echo "Detail endpoint: http://localhost:7788/v/<VIDEO_ID>"