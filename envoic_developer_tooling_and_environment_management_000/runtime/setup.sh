#!/usr/bin/env bash
set -euo pipefail

echo "=== Setting up envoic evaluation environment ==="

# Ensure uv/uvx is on PATH
export PATH="/root/.local/bin:/root/.cargo/bin:$PATH"

# Verify tools are available
echo "--- Checking uvx ---"
uvx --version || echo "uvx not found, falling back to pip-installed envoic"

echo "--- Checking npx ---"
npx --version

echo "--- Checking envoic (pip) ---"
python3 -m envoic --help 2>/dev/null || envoic --help 2>/dev/null || echo "envoic cli via pip"

echo "--- Checking envoic (npm) ---"
npx envoic --help 2>/dev/null || echo "envoic via npx"

echo "--- Workspace top-level ---"
ls -la /workspace/

echo "=== Setup complete ==="