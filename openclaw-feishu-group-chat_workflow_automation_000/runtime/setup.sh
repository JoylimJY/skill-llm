#!/bin/bash
set -e

# Make the sync script executable
chmod +x /workspace/scripts/sync_feishu_contacts.py

# Ensure ~/.openclaw exists and config is accessible
mkdir -p ~/.openclaw

# Verify the mock script runs correctly (smoke test)
python3 /workspace/scripts/sync_feishu_contacts.py --help 2>/dev/null || true

echo "[setup] Workspace ready."
echo "[setup] Key files:"
ls /workspace/*.md /workspace/*.json /workspace/scripts/ 2>/dev/null || true