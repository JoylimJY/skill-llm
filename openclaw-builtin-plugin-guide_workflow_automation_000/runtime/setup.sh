#!/bin/bash
set -e

# Ensure mock openclaw is on PATH
export PATH="/workspace/scripts:$PATH"
echo 'export PATH="/workspace/scripts:$PATH"' >> /etc/environment
echo 'export PATH="/workspace/scripts:$PATH"' >> /root/.bashrc

# Make scripts executable (redundant safety)
chmod +x /workspace/scripts/openclaw
chmod +x /workspace/scripts/openclaw_plugin_catalog.py

# Quick smoke-test the mock CLI
echo "[setup] Verifying mock openclaw CLI..."
/workspace/scripts/openclaw plugins list --json | python3 -c "import sys,json; d=json.load(sys.stdin); assert len(d)==8, f'Expected 8 plugins, got {len(d)}'"
echo "[setup] Mock CLI OK. Workspace ready."