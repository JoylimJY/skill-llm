#!/usr/bin/env bash
set -e

# Ensure the main reconciliation script is executable
chmod +x /workspace/scripts/main.py

# Verify the script is syntactically valid Python
python -m py_compile /workspace/scripts/main.py
echo "[setup] scripts/main.py compiled OK"

# Quick smoke test with the --example flag to confirm the tool is functional
python /workspace/scripts/main.py --example > /dev/null
echo "[setup] scripts/main.py --example smoke test passed"

echo "[setup] Sandbox ready."