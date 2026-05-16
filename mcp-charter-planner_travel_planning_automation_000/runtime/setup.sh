#!/usr/bin/env bash
set -e

echo "=== Charter Planner Sandbox Setup ==="

# Pre-cache the npx package so agent invocations are faster
echo "Pre-fetching MCP charter planner package..."
npx --yes @vbotholemu/mcp-charter-planner --help 2>/dev/null || true

echo "Verifying Python MCP client library..."
python3 -c "import mcp; print('mcp version:', mcp.__version__)" 2>/dev/null || \
    python3 -m pip install --break-system-packages mcp anyio -i https://pypi.tuna.tsinghua.edu.cn/simple -q

echo "Workspace contents:"
ls /workspace/

echo "Setup complete."