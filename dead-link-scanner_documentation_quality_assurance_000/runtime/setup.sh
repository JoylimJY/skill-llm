#!/bin/bash
set -e

# Start the mock staging site server in the background
cd /workspace/staging_site
python3 mock_server.py &
FLASK_PID=$!
echo "Mock server started with PID $FLASK_PID on port 7891"

# Wait until it's accepting connections
for i in $(seq 1 20); do
    if curl -s http://localhost:7891/ > /dev/null 2>&1; then
        echo "Mock server is ready."
        break
    fi
    sleep 0.5
done

echo "Setup complete."