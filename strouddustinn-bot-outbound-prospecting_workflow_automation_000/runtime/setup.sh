#!/usr/bin/env bash
set -e

# Make tool scripts executable (belt-and-suspenders)
chmod +x /workspace/scripts/web_search
chmod +x /workspace/scripts/web_fetch

# Add tool scripts to PATH
echo 'export PATH="/workspace/scripts:$PATH"' >> /etc/profile
export PATH="/workspace/scripts:$PATH"

# Start the mock server in the background
python3 /workspace/scripts/mock_server.py &
MOCK_PID=$!
echo "Mock server PID: $MOCK_PID"

# Wait for mock server to be ready
for i in $(seq 1 15); do
    if curl -s "http://localhost:8765/search?q=test" > /dev/null 2>&1; then
        echo "Mock server is ready."
        break
    fi
    sleep 1
done

# Verify tools work
echo "--- Verifying web_search tool ---"
/workspace/scripts/web_search "bridgepoint engineering group official website" || echo "web_search check done"
echo "--- Verifying web_fetch tool ---"
/workspace/scripts/web_fetch "http://localhost:8765/homepage" | head -5 || echo "web_fetch check done"

echo "Setup complete."