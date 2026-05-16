#!/bin/bash
set -e

echo "=== Starting mock Sina Finance API server ==="
cd /workspace

# Start mock server in background
python3 /workspace/tools/scripts/mock_sina_server.py &
MOCK_PID=$!
echo "Mock server PID: $MOCK_PID"

# Wait for server to start
sleep 2

# Verify server is running
curl -s "http://localhost:18888/list=sh600036" | head -c 100
echo ""
echo "Mock server is running."

# Ensure all scripts are executable
chmod +x /workspace/skills/a-stock-analysis/scripts/analyze.py
chmod +x /workspace/skills/a-stock-analysis/scripts/portfolio.py
chmod +x /workspace/tools/scripts/mock_sina_server.py

# Install uv if not present
pip install uv -i https://pypi.tuna.tsinghua.edu.cn/simple -q

# Create skill pyproject.toml so uv run works
mkdir -p /workspace/skills/a-stock-analysis
cat > /workspace/skills/a-stock-analysis/pyproject.toml << 'EOF'
[project]
name = "a-stock-analysis"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["requests", "flask"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
EOF

echo "=== Setup complete ==="