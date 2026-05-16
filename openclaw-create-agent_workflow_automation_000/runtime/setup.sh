#!/usr/bin/env bash
set -e

# Make scripts executable
chmod +x /workspace/scripts/create_workspace.sh
chmod +x /workspace/scripts/register_agent.py
chmod +x /workspace/scripts/verify_workspace.sh

# Ensure HOME-based openclaw dir exists (agent will create subdirs)
mkdir -p "$HOME/.openclaw/agency-agents"
mkdir -p "$HOME/.openclaw/backups"

# Symlink HOME .openclaw to workspace .openclaw so scripts operate consistently
# and eval can find artifacts predictably
if [ ! -L "$HOME/.openclaw" ]; then
    # Only symlink if HOME != /workspace
    if [ "$HOME" != "/workspace" ]; then
        # Remove if exists as dir, then link
        rm -rf "$HOME/.openclaw"
        ln -sf /workspace/.openclaw "$HOME/.openclaw"
    fi
fi

# Mock openclaw binary (validate always passes)
cat > /usr/local/bin/openclaw << 'EOF'
#!/usr/bin/env bash
if [[ "$1" == "config" && "$2" == "validate" ]]; then
    echo "✅ openclaw config validate: OK"
    exit 0
fi
echo "openclaw: unknown command '$@'" >&2
exit 1
EOF
chmod +x /usr/local/bin/openclaw

# Mock systemctl --user restart (records that restart was called)
# We wrap it so it doesn't fail in a container without systemd
cat > /usr/local/bin/systemctl << 'EOF'
#!/usr/bin/env bash
# Mock systemctl for container environment
echo "[mock systemctl] $@"
if [[ "$*" == *"restart openclaw-gateway.service"* ]]; then
    echo "[mock systemctl] openclaw-gateway.service restarted (mock)"
    echo "restarted" > /workspace/tmp/gateway_restart.txt
fi
exit 0
EOF
chmod +x /usr/local/bin/systemctl

mkdir -p /workspace/tmp

echo "Setup complete. Mock binaries ready."
echo "  openclaw: $(which openclaw)"
echo "  systemctl: $(which systemctl)"