#!/bin/bash
set -e

WORKSPACE=/workspace

# Make scripts executable
chmod +x "$WORKSPACE/scripts/analyze.py"
chmod +x "$WORKSPACE/scripts/portfolio.py"
chmod +x "$WORKSPACE/scripts/mock_server.py"

# Create uv virtual environment for scripts
cd "$WORKSPACE"
uv venv --python 3.11 .venv 2>/dev/null || true

# Install dependencies into the venv used by uv run
uv pip install requests flask --quiet -i https://pypi.tuna.tsinghua.edu.cn/simple 2>/dev/null || true
pip install requests flask --quiet -i https://pypi.tuna.tsinghua.edu.cn/simple 2>/dev/null || true

# Start mock server in background
export FLASK_ENV=production
nohup python3 "$WORKSPACE/scripts/mock_server.py" > /tmp/mock_server.log 2>&1 &
MOCK_PID=$!
echo $MOCK_PID > /tmp/mock_server.pid

# Wait for mock server to be ready
echo "Waiting for mock server to start..."
for i in $(seq 1 20); do
    if curl -s http://localhost:18888/list?list=sh600789 > /dev/null 2>&1; then
        echo "Mock server is ready (pid=$MOCK_PID)"
        break
    fi
    sleep 1
done

# Set environment variables so scripts use mock server
echo "export SINA_MOCK_URL=http://localhost:18888" >> /etc/environment
echo "export EASTMONEY_MOCK_URL=http://localhost:18888" >> /etc/environment
export SINA_MOCK_URL=http://localhost:18888
export EASTMONEY_MOCK_URL=http://localhost:18888

# Create a wrapper env file agents can source
cat > /workspace/.env << 'EOF'
export SINA_MOCK_URL=http://localhost:18888
export EASTMONEY_MOCK_URL=http://localhost:18888
EOF

# Write env vars into /etc/profile.d so all shells pick them up
cat > /etc/profile.d/stock_env.sh << 'EOF'
export SINA_MOCK_URL=http://localhost:18888
export EASTMONEY_MOCK_URL=http://localhost:18888
EOF

echo "Setup complete. Mock server running on port 18888."
echo "Test: curl 'http://localhost:18888/list?list=sh600789'"