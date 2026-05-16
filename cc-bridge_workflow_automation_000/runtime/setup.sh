#!/bin/bash
set -e

# Ensure the mock script is executable
chmod +x /workspace/.openclaw/workspace/skills/cc-bridge/scripts/cc-bridge.sh

# Reset call counter and log
mkdir -p /workspace/tmp/sessions
rm -f /workspace/tmp/sessions/call_log.jsonl
rm -f /workspace/tmp/sessions/call_counter.txt

# Verify the mock script works
echo "Testing mock script..."
RESULT=$(/workspace/.openclaw/workspace/skills/cc-bridge/scripts/cc-bridge.sh "test_session" status)
echo "Mock status result: $RESULT"

# Reset counter again after test
rm -f /workspace/tmp/sessions/call_log.jsonl
rm -f /workspace/tmp/sessions/call_counter.txt

echo "Setup complete. Workspace ready."
echo "Agent task: Process /workspace/incoming_messages.json and produce /workspace/routing_log.json"