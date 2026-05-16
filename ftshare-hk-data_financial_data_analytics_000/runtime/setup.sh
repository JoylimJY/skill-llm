#!/bin/bash
set -e

echo "=== Starting mock server ==="
cd /workspace
python /workspace/mock_server.py &
MOCK_PID=$!
echo "Mock server PID: $MOCK_PID"

# Wait for server to be ready
for i in $(seq 1 15); do
    if curl -sf http://localhost:18888/hk/view?hk_code=02318.HK > /dev/null 2>&1; then
        echo "Mock server is up after ${i} attempts."
        break
    fi
    echo "Waiting for mock server... attempt $i"
    sleep 1
done

# Verify run.py is executable
chmod +x /workspace/skills/hk_data/run.py

echo "=== Environment ready ==="
echo "SKILL.md location: /workspace/skills/hk_data/SKILL.md"
echo "run.py location: /workspace/skills/hk_data/run.py"
echo "Mock server: http://localhost:18888"