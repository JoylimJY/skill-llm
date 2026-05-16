#!/bin/bash
set -e

# Ensure buddy.js is executable
chmod +x /workspace/tools/companion_system/buddy.js

# Create the audit data directory
mkdir -p /workspace/tools/audit/charlie_buddy_data

# Verify node is available
node --version

echo "Setup complete. Workspace ready for agent."
echo "Task ticket: /workspace/onboarding/new_hires/2024/q4/OB-2024-Q4-0089.json"