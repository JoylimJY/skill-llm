#!/usr/bin/env bash
set -e

cd /workspace

# Make the generator script executable
chmod +x scripts/generate-doc-index.ts

# Install tsx globally if not present (already done in Dockerfile, this is a safety net)
which tsx || npm install -g tsx

echo "Setup complete. Workspace ready."
echo ""
echo "Directory layout:"
find /workspace -not -path '*/node_modules/*' -type f | sort