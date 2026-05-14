#!/bin/bash
set -e

echo "[*] Setting up token-optimizer sandbox..."

# Make CLI scripts executable
if [ -f /workspace/token-optimizer/cli.py ]; then
    chmod +x /workspace/token-optimizer/cli.py
    echo "[+] cli.py is executable"
else
    echo "[!] WARNING: cli.py not found at /workspace/token-optimizer/cli.py"
    ls /workspace/token-optimizer/ 2>/dev/null || echo "  (token-optimizer dir missing)"
fi

# Install any dependencies from the cloned repo
if [ -f /workspace/token-optimizer/requirements.txt ]; then
    echo "[*] Installing token-optimizer dependencies..."
    pip install -r /workspace/token-optimizer/requirements.txt \
        -i https://pypi.tuna.tsinghua.edu.cn/simple --quiet
    echo "[+] Dependencies installed"
fi

# Ensure ~/.openclaw structure is correct
mkdir -p ~/.openclaw/backups
mkdir -p ~/.openclaw/workspace
mkdir -p ~/.openclaw/prompts

echo "[+] ~/.openclaw directory structure verified"
echo "[*] Setup complete. Agent workspace ready."
echo ""
echo "Current ~/.openclaw/openclaw.json:"
cat ~/.openclaw/openclaw.json