#!/bin/bash
set -e

# Ensure the stocks skill directory is properly set up
cd /home/user/stocks

# Verify the venv and scripts directory exist
if [ ! -f ".venv/bin/python3" ]; then
    echo "ERROR: Virtual environment not found at /home/user/stocks/.venv"
    exit 1
fi

if [ ! -d "scripts" ]; then
    echo "ERROR: scripts/ directory not found in stocks skill"
    exit 1
fi

# Test that the skill is importable
cd /home/user/stocks/scripts
/home/user/stocks/.venv/bin/python3 - << 'PY'
import sys
sys.path.insert(0, '.')
try:
    from yfinance_ai import Tools
    print("yfinance_ai import: OK")
except ImportError as e:
    print(f"yfinance_ai import FAILED: {e}")
    sys.exit(1)
PY

echo "Setup complete. Skill is ready at /home/user/stocks"
echo "Workspace is at /home/user/workspace"