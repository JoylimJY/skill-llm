#!/usr/bin/env bash
set -e

HOME=/root
MOCK_LOG="$HOME/.openclaw/logs/openclaw-cli-calls.log"

# ─── Create mock `openclaw` CLI ───────────────────────────────────────────────
cat > /usr/local/bin/openclaw << 'MOCK_EOF'
#!/usr/bin/env bash
# Mock openclaw CLI — logs all invocations for eval
LOG_FILE="$HOME/.openclaw/logs/openclaw-cli-calls.log"
mkdir -p "$(dirname "$LOG_FILE")"
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) openclaw $*" >> "$LOG_FILE"

if [[ "$1" == "gateway" && "$2" == "restart" ]]; then
  echo "[openclaw] Gateway restarting..."
  sleep 0.1
  echo "[openclaw] Gateway started on port 9988."
  exit 0
fi

if [[ "$1" == "update" ]]; then
  echo "[openclaw] No updates available."
  exit 0
fi

echo "[openclaw] Unknown command: $*"
exit 1
MOCK_EOF

chmod +x /usr/local/bin/openclaw

# ─── Ensure node is accessible at the NVM-style path ─────────────────────────
NODE_BIN_DIR="$HOME/.nvm/versions/node/v22.22.0/bin"
mkdir -p "$NODE_BIN_DIR"
if [ ! -f "$NODE_BIN_DIR/node" ]; then
    ln -sf "$(which node)" "$NODE_BIN_DIR/node"
fi

# ─── Ensure the openclaw-cli-calls.log exists (empty) ─────────────────────────
mkdir -p "$HOME/.openclaw/logs"
touch "$HOME/.openclaw/logs/openclaw-cli-calls.log"

# ─── Verify key files exist ───────────────────────────────────────────────────
echo "=== Setup complete ==="
echo "node version: $(node --version)"
echo "openclaw mock: $(which openclaw)"
ls "$HOME/.openclaw/workspace/skills/matrix-mentions-patch/"
ls "$HOME/.nvm/versions/node/v22.22.0/lib/node_modules/openclaw/dist/"