#!/bin/bash
set -e

# Ensure the logs and output directories are writable
chmod -R 777 "${WORKSPACE}/pipeline/logs" 2>/dev/null || true
chmod -R 777 "${WORKSPACE}/pipeline/output" 2>/dev/null || true

# Verify entr is available
which entr || (echo "ERROR: entr not found" && exit 1)

echo "Setup complete. entr version: $(entr 2>&1 | head -1 || true)"