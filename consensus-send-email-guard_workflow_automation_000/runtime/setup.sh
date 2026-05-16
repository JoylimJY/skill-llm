#!/bin/bash
set -e

echo "[setup] Configuring workspace permissions..."
chmod -R 755 /workspace
chmod 777 /workspace/state/artifacts
chmod 777 /workspace/state

echo "[setup] Verifying Node.js and tsx are available..."
node --version
tsx --version

echo "[setup] Verifying consensus-send-email-guard is installed..."
# Check if the package is installed globally
npm list -g consensus-send-email-guard 2>/dev/null || echo "[setup] Package may need local install"

echo "[setup] Setting up local npm project in workspace for reliable module access..."
cd /workspace
# Initialize package.json if not present
if [ ! -f package.json ]; then
    npm init -y > /dev/null 2>&1
fi

# Install consensus-send-email-guard locally as well for reliable require()
npm install consensus-send-email-guard 2>&1 | tail -5

echo "[setup] Verifying installation..."
ls /workspace/node_modules/consensus-send-email-guard/ 2>/dev/null && echo "[setup] Package found in local node_modules" || echo "[setup] Check global install"

echo "[setup] Setup complete."