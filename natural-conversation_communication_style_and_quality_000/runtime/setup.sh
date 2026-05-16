#!/bin/bash
set -e

# Ensure workspace permissions are correct
chmod -R 755 /workspace

echo "Workspace ready. Draft replies available at /workspace/draft_replies.json"
echo "Agent should produce /workspace/natural_replies.json"