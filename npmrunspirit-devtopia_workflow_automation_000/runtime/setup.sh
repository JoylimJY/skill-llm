#!/usr/bin/env bash
set -e

echo "=== Devtopia Sandbox Setup ==="

# Verify devtopia is installed
devtopia --version || true

# Run devtopia start to initialise any local state (non-interactive, just read rules)
echo "--- devtopia start ---"
devtopia start --help 2>/dev/null || devtopia start 2>/dev/null | head -40 || true

echo "--- devtopia ls (sampling available tools) ---"
devtopia ls 2>/dev/null | head -20 || true

echo "=== Setup complete ==="