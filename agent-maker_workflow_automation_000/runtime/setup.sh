#!/bin/bash
set -euo pipefail

# Make all scripts in tools/ executable
chmod +x /workspace/tools/*.sh 2>/dev/null || true

# Verify the OpenClaw directory structure was created
echo "=== Verifying sandbox environment ==="
ls -la "$HOME/.openclaw/workspace/skills/" 2>/dev/null && echo "Skills dir OK" || echo "Skills dir missing"
ls -la "$HOME/.openclaw/workspace/agents/" 2>/dev/null && echo "Agents dir OK" || echo "Agents dir missing"

echo "=== Setup complete ==="