#!/usr/bin/env bash
set -e

# Ensure skill script is executable
chmod +x /workspace/skills/approve-pairing/scripts/approve_pairing.py

# Write task description visible to agent
cat > /workspace/TASK.md << 'EOF'
# Pending Messaging Gateway Approvals

Two colleagues have submitted connection requests to our internal messaging relay
and are waiting to be authorized. The admin CLI is not available in this environment.

Please approve both pending requests using the codes they provided:

1. **Telegram** – Priya Sharma sent code: `ALPHA77X`
2. **Slack**    – Marcus Webb  sent code: `BETA99Z`

Both approvals must be completed so the relay accepts their incoming messages.
EOF

echo "setup_script: environment ready."