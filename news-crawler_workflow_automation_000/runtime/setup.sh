#!/usr/bin/env bash
set -e

# Make scripts executable
chmod +x /workspace/scripts/rss_fetcher.py
chmod +x /workspace/scripts/crawl.py
chmod +x /workspace/scripts/mock_server.py

# Start mock HTTP server in background
cd /workspace
python3 scripts/mock_server.py &
MOCK_PID=$!
echo "Mock server started with PID $MOCK_PID"

# Wait for server to be ready
MAX_WAIT=15
COUNT=0
until curl -sf http://localhost:8765/feed.rss > /dev/null 2>&1; do
    sleep 1
    COUNT=$((COUNT+1))
    if [ $COUNT -ge $MAX_WAIT ]; then
        echo "ERROR: Mock server did not start within ${MAX_WAIT} seconds"
        exit 1
    fi
done

echo "Mock server is ready at http://localhost:8765"
echo "RSS feed available at: http://localhost:8765/feed.rss"
echo ""
echo "Workspace is ready. The agent task can now begin."