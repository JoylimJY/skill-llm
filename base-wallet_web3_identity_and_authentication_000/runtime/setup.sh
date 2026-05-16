#!/bin/bash
set -e

# Make scripts executable
chmod +x /workspace/scripts/create-wallet.js
chmod +x /workspace/scripts/check-balance.js
chmod +x /workspace/scripts/basemail-register.js

# Ensure node_modules with ethers is accessible from workspace scripts
# The npm install was done at /workspace level in Dockerfile
ls /workspace/node_modules/ethers > /dev/null 2>&1 && echo "ethers.js available" || echo "WARNING: ethers not found"

# Ensure openclaw wallet dir will be creatable
mkdir -p ~/.openclaw/wallets

# Ensure base-wallet audit log dir exists
mkdir -p ~/.base-wallet

echo "Setup complete. Workspace ready for agent."