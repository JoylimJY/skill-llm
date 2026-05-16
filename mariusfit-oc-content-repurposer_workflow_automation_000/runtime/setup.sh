#!/bin/bash
set -e

# Make scripts executable
chmod +x /workspace/scripts/repurpose.py

# Ensure uv is available
pip install uv -i https://pypi.tuna.tsinghua.edu.cn/simple -q

echo "Setup complete. Workspace ready."
ls /workspace/scripts/