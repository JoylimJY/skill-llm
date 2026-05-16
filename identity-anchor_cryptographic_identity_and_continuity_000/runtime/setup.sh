#!/bin/bash
set -e

# Ensure identity.py is executable
chmod +x /workspace/skills/identity-anchor/scripts/identity.py

# Ensure workspace permissions are correct
chown -R root:root /workspace

echo "Setup complete."
echo "Skill script available at: /workspace/skills/identity-anchor/scripts/identity.py"
echo "Agent persona files at: /workspace/research-agent/persona/"