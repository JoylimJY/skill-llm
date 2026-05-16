#!/usr/bin/env bash
set -e

chmod +x /workspace/skills/bulk-tiktok-downloader/scripts/downloader.py

echo "=== Skill setup: installing requirements ==="
pip install -r /workspace/skills/bulk-tiktok-downloader/scripts/requirements.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple --quiet

echo "=== Setup complete ==="