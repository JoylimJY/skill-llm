#!/bin/bash
set -e

echo "=== Setting up fintech workspace ==="

# Install Node.js dependencies for api-gateway
cd /workspace/api-gateway
npm install --prefer-offline 2>/dev/null || npm install
echo "Node.js deps installed"

# Install Python dependencies for risk-scorer
cd /workspace/risk-scorer
pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --quiet
echo "Python deps installed"

# Ensure pip-audit is available
pip3 install pip-audit -i https://pypi.tuna.tsinghua.edu.cn/simple --quiet 2>/dev/null || true

# Ensure depcheck is globally available
npm install -g depcheck 2>/dev/null || true

cd /workspace
echo "=== Setup complete ==="
echo "Workspace contains:"
echo "  - api-gateway/ (Node.js: express, lodash, axios, helmet, moment, jsonwebtoken)"
echo "  - risk-scorer/ (Python: numpy, scikit-learn, flask, cryptography, pandas, requests)"