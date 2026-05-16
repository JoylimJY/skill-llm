#!/usr/bin/env bash
set -euo pipefail

echo "=== Setting up evaluation environment ==="

# Ensure the mock openclaw is executable
chmod +x /usr/local/bin/openclaw

# Verify mock openclaw works
echo "Testing mock openclaw..."
openclaw agents list

# Initialize clean state (reset any previous runs)
echo '{"agents": []}' > /tmp/openclaw_state.json
echo "Reset openclaw state to empty."

# Create the home directory for root user (needed for ~/.openclaw paths)
mkdir -p /root/.openclaw
echo "Ensured /root/.openclaw exists."

# Confirm skill directory is accessible
if [ -f "/opt/openclaw-skills/content-creation/SKILL.md" ]; then
    echo "SKILL.md found at /opt/openclaw-skills/content-creation/SKILL.md"
else
    echo "WARNING: SKILL.md not found!"
fi

if [ -f "/opt/openclaw-skills/content-creation/templates/USER.md" ]; then
    echo "USER.md template found."
else
    echo "WARNING: USER.md template not found!"
fi

echo "=== Setup complete ==="