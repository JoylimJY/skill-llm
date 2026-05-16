#!/bin/bash
set -e

cd /workspace

# Ensure molt-life-kernel is available locally (in case global install path differs)
npm install molt-life-kernel --save 2>/dev/null || true

# Make the maintenance script executable (distractor)
chmod +x scripts/maintenance/cleanup_old_logs.sh

echo "Setup complete. molt-life-kernel available."
node -e "require('molt-life-kernel'); console.log('molt-life-kernel import OK');"