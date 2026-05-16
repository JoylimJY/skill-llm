#!/bin/bash
set -e

# Create the mock `openclaw` CLI that returns a restricted set of available models.
# CRITICAL: o3 (openai) is NOT in the list — the agent must discover this and fall back.
# gemini-ultra is also absent. Only anthropic models + gpt-4o are available.
cat > /workspace/bin/openclaw << 'CLAWEOF'
#!/bin/bash
if [[ "$1" == "models" && "$2" == "list" ]]; then
    echo "Available models (configured providers only):"
    echo ""
    echo "  anthropic:"
    echo "    - claude-opus-4-6     [deep/research]  thinking: supported"
    echo "    - claude-sonnet       [balanced]        thinking: not supported"
    echo "    - claude-haiku-4-5    [quick]           thinking: not supported"
    echo ""
    echo "  openai:"
    echo "    - gpt-4o              [balanced]        thinking: not supported"
    echo ""
    echo "Note: providers not listed above are not configured in this environment."
else
    echo "openclaw: unknown command '$@'"
    exit 1
fi
CLAWEOF

chmod +x /workspace/bin/openclaw

# Make the bin directory discoverable
export PATH="/workspace/bin:$PATH"
echo 'export PATH="/workspace/bin:$PATH"' >> /root/.bashrc
echo 'export PATH="/workspace/bin:$PATH"' >> /root/.profile

# Verify mock works
echo "--- Verifying mock openclaw ---"
/workspace/bin/openclaw models list

echo "--- Setup complete ---"