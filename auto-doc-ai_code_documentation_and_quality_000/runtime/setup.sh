#!/bin/bash
set -e

echo "=== Setting up auto-doc-ai skill environment ==="

# Install the auto-doc-ai skill if available via the skill mechanism
# The skill exposes /generate-docs as a command
cd /workspace

# Check if /generate-docs is already available (pre-installed skill)
if command -v /generate-docs &> /dev/null; then
    echo "/generate-docs found at system level"
elif [ -f "/usr/local/bin/generate-docs" ]; then
    echo "generate-docs found in /usr/local/bin"
else
    echo "Attempting to install auto-doc-ai skill..."
    # Try pip install if packaged
    pip install auto-doc-ai -i https://pypi.tuna.tsinghua.edu.cn/simple 2>/dev/null || true
fi

echo "=== Workspace structure ==="
find /workspace/src -type f -name "*.py" | sort

echo "=== Setup complete ==="