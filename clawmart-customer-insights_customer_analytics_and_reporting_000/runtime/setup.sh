#!/bin/bash
set -e

# Ensure scripts are executable
chmod +x /workspace/scripts/*.sh 2>/dev/null || true
chmod +x /workspace/scripts/*.py 2>/dev/null || true

# Verify raw data is present
echo "=== Workspace verification ==="
ls /workspace/raw_data/
ls /workspace/raw_data/wechat/
ls /workspace/raw_data/email/
ls /workspace/raw_data/crm/
echo "=== Setup complete ==="