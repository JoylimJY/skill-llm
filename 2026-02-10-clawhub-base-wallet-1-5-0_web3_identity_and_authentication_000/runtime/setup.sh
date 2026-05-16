#!/bin/bash
set -e

echo "=== Setting up Base Wallet evaluation environment ==="

# Ensure scripts are executable
chmod +x /workspace/scripts/create-wallet.js
chmod +x /workspace/scripts/check-balance.js
chmod +x /workspace/scripts/basemail-register.js

# Ensure node_modules are accessible from workspace
if [ ! -d "/workspace/node_modules" ]; then
    ln -s /node_modules /workspace/node_modules 2>/dev/null || true
fi

# Create audit log directory
mkdir -p ~/.base-wallet
mkdir -p ~/.openclaw/wallets

# Verify ethers is importable
node -e "const { ethers } = require('ethers'); console.log('ethers version:', ethers.version);"

echo "=== Setup complete ==="