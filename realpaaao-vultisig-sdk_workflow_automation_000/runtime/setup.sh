#!/bin/bash
set -e

echo "Setting up workspace..."

cd /workspace

# @vultisig/sdk is not on public registry - skip install for static analysis only
echo "Note: @vultisig/sdk is not on public registry - skipping install (static analysis only)"

echo "Workspace ready."
ls -la /workspace/treasury/scripts/