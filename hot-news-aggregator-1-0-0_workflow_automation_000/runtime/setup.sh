#!/bin/bash
set -e

chmod +x /workspace/scripts/mock_news_server.py

# Start the mock news server in the background
cd /workspace
python /workspace/scripts/mock_news_server.py &
MOCK_PID=$!
echo "Mock news server started with PID $MOCK_PID"

# Wait for server to be ready
for i in $(seq 1 15); do
    if python -c "import urllib.request; urllib.request.urlopen('http://localhost:8765/api/all')" > /dev/null 2>&1; then
        echo "Mock server is ready on port 8765"
        break
    fi
    echo "Waiting for mock server... ($i/15)"
    sleep 1
done

# Verify server is responding
echo "Verifying server endpoints..."
python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8765/36kr').read().decode()[:200])"
python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8765/techcrunch').read().decode()[:200])"
echo "Setup complete."