#!/usr/bin/env bash
set -e

WORKSPACE="${WORKSPACE:-/workspace}"

echo "[setup] Starting mock Discogs API server..."
cd "$WORKSPACE"

python3 skills/discogs-cli/mock_server.py &
MOCK_PID=$!
echo "$MOCK_PID" > /tmp/mock_server.pid

# Wait for mock server to be ready
for i in $(seq 1 15); do
    if curl -sf http://127.0.0.1:8765/database/search?q=test > /dev/null 2>&1; then
        echo "[setup] Mock server is ready on port 8765 (PID=$MOCK_PID)"
        break
    fi
    sleep 1
done

# Pre-populate the config with the mock base URL so config set --base-url is available
# but we also write a hint file that the base URL for the local mock is http://127.0.0.1:8765
# The agent must still use config set with -u and -t flags (the proprietary trap)
cat > /tmp/discogs_env_info.txt <<'EOF'
Mock Discogs API is running locally at: http://127.0.0.1:8765
Username to use: vinyl_tester
Token to use: mock_token_abc123
EOF

echo "[setup] Environment info written to /tmp/discogs_env_info.txt"
echo "[setup] Setup complete."