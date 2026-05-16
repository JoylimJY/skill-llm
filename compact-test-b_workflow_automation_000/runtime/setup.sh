#!/bin/bash
set -e

echo "=== Smart Compact Sandbox Setup ==="

# Make scripts executable
find /workspace/scripts -name "*.sh" -exec chmod +x {} \;

# Ensure memory directory exists and is writable
chmod 755 /workspace/memory

# Display workspace structure for agent orientation
echo "=== Workspace Structure ==="
find /workspace -type f | sort | head -40

echo "=== Memory Directory ==="
ls -la /workspace/memory/

TODAY=$(date +%Y-%m-%d)
echo "=== Existing Memory File (memory/${TODAY}.md) ==="
cat /workspace/memory/${TODAY}.md

echo "=== Session Log Preview ==="
head -20 /workspace/session_log.txt

echo "=== Setup Complete ==="