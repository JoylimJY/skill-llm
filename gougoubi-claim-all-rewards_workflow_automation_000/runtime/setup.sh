#!/bin/bash
set -e

# Make all scripts executable
chmod +x /workspace/scripts/pbft-claim-rewards-profile-method.mjs
chmod +x /workspace/scripts/pbft-claim-rewards-quick.mjs
chmod +x /workspace/scripts/pbft-claim-three-address-rewards.mjs

# Verify Node.js is available
node --version

# Quick smoke test of profile script help
node /workspace/scripts/pbft-claim-rewards-profile-method.mjs --help

echo "Setup complete."