#!/bin/bash
set -e

cd /workspace

echo "=== Installing Node.js dependencies ==="
npm install --legacy-peer-deps 2>/dev/null || true

echo "=== Verifying pip-audit is installed ==="
pip3 show pip-audit > /dev/null 2>&1 || pip3 install pip-audit -i https://pypi.tuna.tsinghua.edu.cn/simple

echo "=== Setup complete ==="