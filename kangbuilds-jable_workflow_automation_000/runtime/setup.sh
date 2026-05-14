#!/usr/bin/env bash
set -e

WORKSPACE="${WORKSPACE:-/workspace}"

# Make scripts executable
chmod +x "$WORKSPACE/skills/jable/scripts/top_liked_recent.py"
chmod +x "$WORKSPACE/mock_server/server.py"

# Start the mock Flask server in background
echo "Starting mock Jable server on port 18888..."
JABLE_BASE_URL=http://localhost:18888 \
  python3 "$WORKSPACE/mock_server/server.py" \
  > "$WORKSPACE/logs/mock_server.log" 2>&1 &

SERVER_PID=$!
echo $SERVER_PID > "$WORKSPACE/logs/mock_server.pid"

# Wait for server to be ready (up to 15 seconds)
for i in $(seq 1 15); do
  if curl -sf http://localhost:18888/rss/ > /dev/null 2>&1; then
    echo "Mock server is up (PID=$SERVER_PID)"
    break
  fi
  echo "Waiting for mock server... ($i/15)"
  sleep 1
done

# Export the base URL override so the skill script points to local server
export JABLE_BASE_URL=http://localhost:18888
echo "JABLE_BASE_URL=http://localhost:18888" >> /etc/environment

# Verify the mock endpoints work
echo "--- RSS Feed Check ---"
curl -sf http://localhost:18888/rss/ | head -5
echo ""
echo "--- Latest Updates Page 1 Check ---"
curl -sf "http://localhost:18888/latest-updates/" | grep -o 'like-count.*</span>' | head -3
echo ""
echo "Setup complete. Mock server running at http://localhost:18888"