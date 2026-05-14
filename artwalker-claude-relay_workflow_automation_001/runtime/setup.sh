#!/usr/bin/env bash
set -euo pipefail

echo "=== Claude Relay Sandbox Setup ==="

# Start tmux server in background (needed for relay.sh to work)
tmux start-server 2>/dev/null || true

# Ensure relay.sh is executable
chmod +x /workspace/skills/claude-relay/scripts/relay.sh

# Ensure fake claude is executable
chmod +x /workspace/bin/fake_claude

# Export env vars for the session - write to a global profile so the agent can source it
cat > /workspace/.relay_test_env <<'EOF'
export CLAUDE_BIN=/workspace/bin/fake_claude
export CLAUDE_RELAY_ROOT=/workspace/fintech_projects
export CLAUDE_RELAY_MAP=/workspace/config/relay/projects.map
export RELAY_WAIT=1
export PATH=/workspace/bin:$PATH
EOF

# Also set them in /etc/environment for persistence across shells
echo "CLAUDE_BIN=/workspace/bin/fake_claude" >> /etc/environment
echo "CLAUDE_RELAY_ROOT=/workspace/fintech_projects" >> /etc/environment
echo "CLAUDE_RELAY_MAP=/workspace/config/relay/projects.map" >> /etc/environment
echo "RELAY_WAIT=1" >> /etc/environment

# Source into current shell profile
cat >> /root/.bashrc <<'EOF'
source /workspace/.relay_test_env 2>/dev/null || true
EOF

cat >> /root/.profile <<'EOF'
source /workspace/.relay_test_env 2>/dev/null || true
EOF

echo "Setup complete."
echo "Mock claude: /workspace/bin/fake_claude"
echo "Relay script: /workspace/skills/claude-relay/scripts/relay.sh"
echo "Custom map: /workspace/config/relay/projects.map"
echo "Projects root: /workspace/fintech_projects"

# Verify tmux works
tmux new-session -d -s test_setup "echo ok" 2>/dev/null || true
sleep 0.5
tmux kill-session -t test_setup 2>/dev/null || true
echo "tmux verified."