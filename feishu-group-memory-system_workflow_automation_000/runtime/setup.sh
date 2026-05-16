#!/bin/bash
set -e

# Make scripts executable
chmod +x /workspace/scripts/cleanup.sh 2>/dev/null || true

# Create the FeishuGroupMemory directory under the standard path as well
mkdir -p ~/.openclaw/workspace/memory/FeishuGroupMemory 2>/dev/null || true

# Verify workspace structure
echo "=== Workspace Structure ==="
tree /workspace --dirsfirst -a 2>/dev/null || find /workspace -type f | sort

echo ""
echo "=== Key files for task ==="
echo "--- Existing Group Memory (MUST NOT BE OVERWRITTEN) ---"
cat /workspace/memory/FeishuGroupMemory/oc_1736efe0d350b597267e3ed59bcc8f42.md
echo ""
echo "--- Today's Daily Memory (MUST HAVE GROUP SECTION APPENDED) ---"
cat /workspace/memory/2026-04-15.md
echo ""
echo "--- Raw Session Data to Archive ---"
cat /workspace/sessions/session_2026-04-15_engineering.md
echo ""
echo "=== Setup complete. Agent may begin. ==="