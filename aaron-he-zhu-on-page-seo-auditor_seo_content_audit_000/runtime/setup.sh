#!/bin/bash
set -e

chmod +x /workspace/scripts/mock_server.py
chmod +x /workspace/scripts/generate-sitemap.py

# Start the mock server in background
python3 /workspace/scripts/mock_server.py &
MOCK_PID=$!
echo "Mock server started with PID $MOCK_PID"

# Wait for the server to be ready
for i in $(seq 1 20); do
    if curl -sf http://localhost:8765/ > /dev/null 2>&1; then
        echo "Mock server is ready."
        break
    fi
    echo "Waiting for mock server... ($i/20)"
    sleep 1
done

# Verify it's serving content
curl -sf http://localhost:8765/eco-camping-gear | grep -q "TrailPeak" && echo "Mock server verified OK." || echo "WARNING: Mock server may not be serving correctly."