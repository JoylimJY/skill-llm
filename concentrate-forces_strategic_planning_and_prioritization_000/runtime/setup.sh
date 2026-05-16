#!/bin/bash
set -e

# Ensure workspace permissions are correct
chmod -R 755 /workspace

# Verify the backlog file was generated
if [ ! -f /workspace/backlog.json ]; then
    echo "ERROR: backlog.json not found!"
    exit 1
fi

echo "Workspace ready. backlog.json present with $(jq '.initiatives | length' /workspace/backlog.json) initiatives."
echo "Agent task: analyze backlog.json and produce execution_plan.json"