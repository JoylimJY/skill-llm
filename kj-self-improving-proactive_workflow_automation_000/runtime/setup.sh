#!/bin/bash
set -e

echo "=== Setup: Verifying workspace ==="
ls /workspace/
echo "=== Memory directories ==="
ls ~/self-improving/ 2>/dev/null || echo "self-improving dir missing"
ls ~/proactivity/ 2>/dev/null || echo "proactivity dir missing"
echo "=== Setup complete ==="