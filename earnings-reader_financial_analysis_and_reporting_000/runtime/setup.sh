#!/usr/bin/env bash
set -euo pipefail

# Ensure the mock script is executable
chmod +x /workspace/skills/akshare-finance/scripts/earnings.py

# Verify python3.12 is available and the mock script works
echo "=== Verifying mock earnings script ==="
python3.12 /workspace/skills/akshare-finance/scripts/earnings.py report 000858 | head -5
echo "=== Mock script OK ==="

# Ensure output directory exists and is writable
mkdir -p /workspace/output
chmod 777 /workspace/output

echo "Setup complete."