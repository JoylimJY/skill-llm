#!/bin/bash
set -e

# Ensure openclaw CLI is executable
chmod +x /usr/local/bin/openclaw

# Ensure the upsert script is executable
chmod +x /workspace/skills/openclaw-create-agent/scripts/upsert_openclaw_agent.py

# Ensure ~/.openclaw exists and has correct permissions
mkdir -p /root/.openclaw
chmod 700 /root/.openclaw

# Seed the agents file so the existing agent is registered
cat > /root/.openclaw/agents.json << 'EOF'
{
  "agents": [
    {
      "id": "ops-assistant",
      "workspace": "/workspace/agents/ops-assistant",
      "model": "gpt-4o"
    }
  ]
}
EOF

# Clear any stale gateway state
rm -f /root/.openclaw/gateway_state

echo "Setup complete. OpenClaw mock environment ready."
echo "Existing config:"
cat /root/.openclaw/openclaw.json