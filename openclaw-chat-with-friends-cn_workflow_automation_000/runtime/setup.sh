#!/bin/bash
set -e

echo "Setting up OpenClaw channel configuration task..."

# Make workspace writable
chmod -R 777 /workspace

# Create a simple mock OpenClaw CLI that verifies AGENTS.md exists
cat > /usr/local/bin/openclaw-verify << 'EOF'
#!/bin/bash
# Mock OpenClaw verification tool
AGENTS_FILE=$(find /workspace -name "AGENTS.md" | head -1)
if [ -z "$AGENTS_FILE" ]; then
    echo "ERROR: No AGENTS.md found in workspace"
    exit 1
fi
echo "Found AGENTS.md at: $AGENTS_FILE"
echo "Verification complete."
EOF
chmod +x /usr/local/bin/openclaw-verify

echo "Setup complete. Task workspace ready."
echo "The agent must create/update the AGENTS.md configuration file for the OpenClaw channel."