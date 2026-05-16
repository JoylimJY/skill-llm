#!/usr/bin/env bash
set -e

chmod +x /workspace/scripts/mock_server.py

# Start the mock Bilibili data server in the background
python3 /workspace/scripts/mock_server.py &
MOCK_PID=$!
echo "Mock server started with PID $MOCK_PID"

# Wait for it to be ready
sleep 2

# Verify it's running
curl -s http://localhost:8765/health && echo "" && echo "Mock server is healthy."

echo "Setup complete. Mock Bilibili data server is available at http://localhost:8765"
echo "Endpoints: /rankings, /season_info, /anime/<rank>, /health"