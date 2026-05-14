#!/bin/bash
set -e

echo "Setting up workspace..."

cd /workspace

# Install npm dependencies (attempt - may fail gracefully if registry unavailable)
npm install --save @vultisig/sdk 2>/dev/null || \
npm install --save @vultisig/sdk --registry https://registry.npmmirror.com 2>/dev/null || \
echo "Note: @vultisig/sdk install attempted (may not be on public registry - static analysis only)"

echo "Workspace ready."
ls -la /workspace/treasury/scripts/