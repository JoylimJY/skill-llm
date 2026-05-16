#!/bin/bash
set -e

export PATH="/root/.bun/bin:$PATH"
cd /workspace

echo "=== Installing root workspace dependencies ==="
# Install with npm (legacy-peer-deps to avoid resolution errors with the messy lockfile)
npm install --legacy-peer-deps 2>&1 | tail -20 || true

echo "=== Installing api-gateway dependencies ==="
cd /workspace/packages/api-gateway
npm install --legacy-peer-deps 2>&1 | tail -10 || true

echo "=== Installing payment-engine dependencies ==="
cd /workspace/packages/payment-engine
npm install --legacy-peer-deps 2>&1 | tail -10 || true

echo "=== Installing shared-utils dependencies ==="
cd /workspace/packages/shared-utils
npm install --legacy-peer-deps 2>&1 | tail -10 || true

echo "=== Installing frontend-admin dependencies ==="
cd /workspace/packages/frontend-admin
# Don't install react-scripts fully (too heavy), just the essentials
npm install --legacy-peer-deps --ignore-scripts 2>&1 | tail -10 || true

echo "=== Setup complete ==="
echo "Workspace ready for npm ls and npm audit commands."