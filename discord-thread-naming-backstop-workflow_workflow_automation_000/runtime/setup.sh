#!/bin/bash
set -e

# Make mock server executable
chmod +x /workspace/mock_discord_server.py

# Start mock Discord API server in background
cd /workspace
nohup python3 mock_discord_server.py > /workspace/mock_server.log 2>&1 &
MOCK_PID=$!
echo "Mock Discord server started with PID $MOCK_PID on port 7788"

# Wait for it to be ready
sleep 2

# Verify it's up
for i in {1..10}; do
    if curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:7788/discord-action \
        -H "Content-Type: application/json" \
        -d '{"action":"thread-list","guildId":"1478785964896817267","channelId":"1478785965580357754","includeArchived":false,"limit":50}' | grep -q "200"; then
        echo "Mock server is ready."
        break
    fi
    echo "Waiting for mock server... ($i)"
    sleep 1
done

echo "Setup complete."