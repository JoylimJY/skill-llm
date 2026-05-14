#!/bin/bash
set -e

echo "=== Setting up Agent Traffic Analyzer workspace ==="

# Verify the CLI tool is installed
if ! command -v agent-traffic-analyzer &> /dev/null; then
    echo "ERROR: agent-traffic-analyzer not found in PATH"
    exit 1
fi

echo "agent-traffic-analyzer version: $(agent-traffic-analyzer --version 2>/dev/null || echo 'installed')"

# Ensure workspace permissions
chmod -R 755 /workspace
chmod +x /workspace/pipeline/tests/test_harness.sh 2>/dev/null || true

echo "=== Setup complete ==="
echo "Log file location: /workspace/ops/order_pipeline_comms_2026_03.json"
echo "Agent should analyze this file and produce a full report."