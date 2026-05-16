#!/bin/bash
set -e

# Initialize call log and state files
touch /tmp/memos_call_log.jsonl
echo '{"installed_skills": [], "published_skills": [], "public_memories": []}' > /tmp/memos_state.json

# Make mock server executable
chmod +x /workspace/memos_mock_server.py
chmod +x /workspace/memos_client_stub.py

# Start the MemOS mock server in the background
cd /workspace
python3 memos_mock_server.py &
MOCK_PID=$!
echo "MemOS mock server started with PID $MOCK_PID"

# Wait for server to be ready
for i in $(seq 1 15); do
    if curl -s http://localhost:8765/health > /dev/null 2>&1; then
        echo "Mock server is ready."
        break
    fi
    echo "Waiting for server... ($i/15)"
    sleep 1
done

# Write the MEMOS_BASE_URL env hint to a file the agent can read
echo "http://localhost:8765" > /workspace/agent_configs/main/memos_endpoint.txt
echo "Setup complete."