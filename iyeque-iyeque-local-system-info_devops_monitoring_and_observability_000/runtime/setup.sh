#!/bin/bash
set -e

# Ensure skill script is executable
chmod +x /workspace/skills/local-system-info/sysinfo.py

# Ensure uv is available
which uv || pip install uv -i https://pypi.tuna.tsinghua.edu.cn/simple

echo "Setup complete."