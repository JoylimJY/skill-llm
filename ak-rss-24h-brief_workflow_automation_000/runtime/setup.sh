#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${WORKSPACE:-/workspace}"

# Make scripts executable
chmod +x "$WORKSPACE/scripts/generate_brief.py"
chmod +x "$WORKSPACE/tools/mock_feed_server.py"
chmod +x "$WORKSPACE/tools/parsers/opml_validator.py"

# Start the mock RSS feed server in background
export WORKSPACE="$WORKSPACE"
python3 "$WORKSPACE/tools/mock_feed_server.py" 18765 &
MOCK_PID=$!
echo "Mock feed server started with PID $MOCK_PID"

# Wait for server to be ready
for i in $(seq 1 10); do
    if curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:18765/feeds/ai-research.xml" | grep -q "200"; then
        echo "Mock feed server is ready."
        break
    fi
    echo "Waiting for mock server... ($i/10)"
    sleep 1
done

echo "Setup complete. Workspace: $WORKSPACE"
echo "OPML file located at: $WORKSPACE/feeds/opml/tech_feeds.opml"
echo ""
echo "Agent task: Generate a 24-hour Chinese technology brief and save it to daily_brief.md"