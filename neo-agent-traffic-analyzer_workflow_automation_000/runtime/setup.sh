#!/bin/bash
set -e

echo "=== Setting up Agent Traffic Analyzer sandbox ==="

# Verify the tool is installed
which agent-traffic-analyzer && echo "agent-traffic-analyzer found" || echo "WARNING: agent-traffic-analyzer not found"

# Make utility scripts executable
chmod +x /workspace/scripts/utils/cleanup.sh 2>/dev/null || true

# Ensure workspace directories exist
mkdir -p /workspace/ops/logs/raw
mkdir -p /workspace/reports

echo "=== Setup complete ==="