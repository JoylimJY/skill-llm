#!/bin/bash
set -e

chmod +x /root/.openclaw/workspace/skills/memory-compact/wrapper.py

echo "Setup complete. Workspace ready."
echo "Memory files:"
ls -la /root/.openclaw/workspace/memory/
echo "Existing MEMORY.md:"
cat /root/.openclaw/workspace/MEMORY.md