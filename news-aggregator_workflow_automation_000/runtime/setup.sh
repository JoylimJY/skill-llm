#!/bin/bash
set -e

chmod +x /workspace/scripts/mock_news_server.py

# Start the mock news server in background
python3 /workspace/scripts/mock_news_server.py &
MOCK_PID=$!
echo "Mock news server started with PID $MOCK_PID"

# Wait for it to be ready
for i in $(seq 1 15); do
    if curl -sf http://localhost:8765/health > /dev/null 2>&1; then
        echo "Mock server is ready."
        break
    fi
    echo "Waiting for mock server... ($i)"
    sleep 1
done

# Verify it's truly up
curl -sf http://localhost:8765/health && echo "Server health check passed." || echo "WARNING: Server may not be ready"

echo "Setup complete. Mock news API available at http://localhost:8765"
echo "Endpoints: /all, /all/tech, /all/military, /36kr/tech, /jiqizhixin, /guancha, /thepaper, /techcrunch, /theverge, /defensenews, /militarytimes"