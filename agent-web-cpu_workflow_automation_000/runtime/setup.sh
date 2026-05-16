#!/bin/bash
set -e

WORKSPACE="${WORKSPACE:-/workspace}"

chmod +x "$WORKSPACE/mock_transweb_server.py" 2>/dev/null || true

# Start the mock transweb server in background
python3 "$WORKSPACE/mock_transweb_server.py" 7788 &
MOCK_PID=$!
echo "Mock server started with PID $MOCK_PID on port 7788"

# Wait for it to be ready
sleep 2

# Verify it's running
curl -s "http://localhost:7788/?id=f7e6d5c4b3a291807f6e5d4c3b2a1908" > /tmp/mock_check.html
if grep -q "科技博客生成器" /tmp/mock_check.html; then
    echo "Mock server verified: app info available"
else
    echo "WARNING: Mock server may not be responding correctly"
    cat /tmp/mock_check.html
fi

echo $MOCK_PID > /tmp/mock_server.pid
echo "Setup complete."