#!/usr/bin/env bash
set -e

chmod +x /workspace/skills/local-system-info/sysinfo.py

# Ensure uv is available
if ! command -v uv &>/dev/null; then
    pip install uv -i https://pypi.tuna.tsinghua.edu.cn/simple
fi

echo "Setup complete."