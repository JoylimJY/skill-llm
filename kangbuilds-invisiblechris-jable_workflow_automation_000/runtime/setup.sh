#!/usr/bin/env bash
set -e

# Make scripts executable
chmod +x /workspace/mock_server_data/mock_server.py
chmod +x /workspace/skills/jable/scripts/top_liked_recent.py

# Start the mock jable.tv server in the background
cd /workspace
FLASK_ENV=production python3 /workspace/mock_server_data/mock_server.py &
MOCK_PID=$!
echo "Mock server started with PID $MOCK_PID"

# Wait for server to be ready
for i in $(seq 1 15); do
    if curl -sf http://localhost:8765/rss/ > /dev/null 2>&1; then
        echo "Mock server is ready."
        break
    fi
    echo "Waiting for mock server... ($i/15)"
    sleep 1
done

# Verify server responds
curl -sf http://localhost:8765/rss/ > /dev/null && echo "RSS endpoint OK" || echo "WARNING: RSS endpoint not responding"
curl -sf http://localhost:8765/latest-updates/ > /dev/null && echo "Latest-updates endpoint OK" || echo "WARNING: latest-updates not responding"

echo "Setup complete. Agent workspace ready at /workspace"
echo "JABLE_BASE_URL environment variable should be set to http://localhost:8765 when running the skill."