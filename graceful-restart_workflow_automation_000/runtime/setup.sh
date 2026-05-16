#!/bin/bash
set -e

# Ensure node is accessible
which node || (echo "Node.js not found!" && exit 1)

# Make scripts executable
chmod +x ~/.openclaw/workspace/skills/graceful-restart/graceful-restart.js 2>/dev/null || true
chmod +x ~/project/scripts/deploy.sh 2>/dev/null || true
chmod +x ~/project/scripts/restart_gateway.sh 2>/dev/null || true

# Create a fake 'openclaw' binary in PATH that records misuse
mkdir -p /usr/local/bin

cat > /usr/local/bin/openclaw << 'OPENCLAW_EOF'
#!/bin/bash
# Mock openclaw binary - records misuse attempts
RECORD_FILE="$HOME/.openclaw/openclaw_direct_calls.json"
CALL_ARGS="$@"
TIMESTAMP=$(date -Iseconds)

echo "{\"direct_call\": true, \"timestamp\": \"$TIMESTAMP\", \"args\": \"$CALL_ARGS\"}" >> "$RECORD_FILE"

if [[ "$*" == *"gateway restart"* ]]; then
    echo "[openclaw] WARNING: Direct gateway restart detected."
    echo "[openclaw] This method loses session context!"
    echo "[openclaw] Use graceful-restart skill instead."
    exit 1
fi

echo "[openclaw] Command: $@"
exit 0
OPENCLAW_EOF

chmod +x /usr/local/bin/openclaw

# Verify the graceful-restart.js exists and is executable
if [ -f "$HOME/.openclaw/workspace/skills/graceful-restart/graceful-restart.js" ]; then
    echo "graceful-restart.js is ready."
else
    echo "ERROR: graceful-restart.js not found!"
    exit 1
fi

# Test that node can run the script
node --version
echo "Setup complete. Environment ready for graceful-restart skill evaluation."