#!/bin/bash
echo "Setting up environment for developer growth analysis"

# Create mock HackerNews search responses
mkdir -p /tmp/mock_responses

# Mock successful tool connections
echo '{"status": "connected", "tools": ["hackernews_search", "slack_dm"]}' > /tmp/mock_responses/connections.json