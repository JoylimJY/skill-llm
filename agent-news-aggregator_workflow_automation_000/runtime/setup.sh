#!/bin/bash
set -e

echo "Starting mock HTTP server..."
cd /workspace
python3 scripts/mock_server.py &
MOCK_PID=$!
echo "Mock server PID: $MOCK_PID"

# Wait for server to be ready
for i in $(seq 1 15); do
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        echo "Mock server is ready."
        break
    fi
    echo "Waiting for mock server... ($i/15)"
    sleep 1
done

# Verify key endpoints
echo "Verifying mock endpoints..."
curl -s http://localhost:8080/blog | grep -q "NovaMind" && echo "  /blog OK" || echo "  /blog FAILED"
curl -s http://localhost:8080/releases | grep -q "v2.5.0" && echo "  /releases OK" || echo "  /releases FAILED"
curl -s http://localhost:8080/news | grep -q "Series B" && echo "  /news OK" || echo "  /news FAILED"

echo "Setup complete. Mock server running on http://localhost:8080"
echo "Workspace structure:"
find /workspace -type f | sort | head -30