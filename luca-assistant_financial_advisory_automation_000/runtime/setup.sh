#!/bin/bash
set -e

export PATH="$HOME/.local/bin:/root/.local/bin:/root/.cargo/bin:$PATH"

echo "=== Luca Assistant Setup ==="

# Check if luca is already installed
if command -v luca-mcp &>/dev/null; then
    echo "luca-mcp already available"
else
    echo "Installing luca-assistant..."
    uv tool install luca-assistant || true
fi

export PATH="$HOME/.local/bin:/root/.local/bin:$PATH"

# Seed the database
echo "Seeding card database..."
luca cards 2>/dev/null | head -3 || true

# Find the luca skill base directory (where scripts/mcp_call.sh lives)
LUCA_SKILL_DIR=""
for candidate in \
    "$(python3 -c 'import luca_assistant; import os; print(os.path.dirname(luca_assistant.__file__))' 2>/dev/null)" \
    "$(uv tool dir)/luca-assistant/lib/python*/site-packages/luca_assistant" \
    "/root/.local/share/uv/tools/luca-assistant/lib/python*/site-packages/luca_assistant" \
    "/root/.local/lib/python*/site-packages/luca_assistant"
do
    if [ -f "$candidate/scripts/mcp_call.sh" ] 2>/dev/null; then
        LUCA_SKILL_DIR="$candidate"
        break
    fi
done

# Also search more broadly
if [ -z "$LUCA_SKILL_DIR" ]; then
    FOUND=$(find /root/.local /usr/local -name "mcp_call.sh" 2>/dev/null | head -1)
    if [ -n "$FOUND" ]; then
        LUCA_SKILL_DIR="$(dirname "$(dirname "$FOUND")")"
    fi
fi

echo "Luca skill dir: $LUCA_SKILL_DIR"

# Write a helper that wraps mcp_call.sh with the correct basedir
cat > /workspace/tools/scripts/luca_call.sh << 'WRAPPER'
#!/bin/bash
export PATH="$HOME/.local/bin:/root/.local/bin:$PATH"
TOOL="$1"
ARGS="$2"

# Find mcp_call.sh
MCP_SCRIPT=$(find /root/.local /usr/local -name "mcp_call.sh" 2>/dev/null | head -1)
if [ -z "$MCP_SCRIPT" ]; then
    echo "ERROR: mcp_call.sh not found" >&2
    exit 1
fi
BASEDIR="$(dirname "$(dirname "$MCP_SCRIPT")")"
bash "$MCP_SCRIPT" "$TOOL" "$ARGS"
WRAPPER
chmod +x /workspace/tools/scripts/luca_call.sh

# Also expose mcp_call.sh path for agents
MCP_SCRIPT=$(find /root/.local /usr/local -name "mcp_call.sh" 2>/dev/null | head -1)
if [ -n "$MCP_SCRIPT" ]; then
    echo "MCP_CALL_SCRIPT=$MCP_SCRIPT" > /workspace/tools/config/luca_paths.env
    BASEDIR="$(dirname "$(dirname "$MCP_SCRIPT")")"
    echo "LUCA_BASEDIR=$BASEDIR" >> /workspace/tools/config/luca_paths.env
    echo "Luca paths written to /workspace/tools/config/luca_paths.env"
fi

echo "=== Setup complete ==="
luca-mcp --help 2>&1 | head -5 || true