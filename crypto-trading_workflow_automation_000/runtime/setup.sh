#!/bin/bash
set -e

echo "=== Starting mock API server ==="
chmod +x /workspace/scripts/mock_server.py
cd /workspace
nohup python3 scripts/mock_server.py > logs/mock_server.log 2>&1 &
echo $! > /tmp/mock_server.pid
sleep 2

# Verify mock server is up
if curl -s http://localhost:5055/account > /dev/null; then
    echo "Mock server running on port 5055"
else
    echo "WARNING: Mock server may not be ready yet"
fi

echo "=== Workspace ready ==="
ls -la /workspace/
echo ""
echo "=== Core files ==="
ls -la /workspace/core/
echo ""
echo "=== Memory files ==="
ls -la /workspace/memory/trading/