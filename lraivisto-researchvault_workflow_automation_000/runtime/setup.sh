#!/usr/bin/env bash
set -euo pipefail

echo "[setup] Installing ResearchVault package via uv..."
cd /workspace

# Ensure uv is available
export PATH="/root/.local/bin:/root/.cargo/bin:$PATH"

# Initialize the uv virtual environment and install the package
uv venv --python 3.13 2>/dev/null || uv venv
uv pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple

echo "[setup] Verifying vault CLI is accessible..."
uv run python scripts/vault.py --help

echo "[setup] Workspace ready."