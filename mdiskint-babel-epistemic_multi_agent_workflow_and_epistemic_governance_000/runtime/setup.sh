#!/bin/bash
set -e

chmod +x /workspace/scripts/validation/run_checks.sh 2>/dev/null || true

# Attempt to install babel-validate if not already present
if ! command -v babel-validate &>/dev/null; then
    npm install -g babel-validate --registry https://registry.npmmirror.com 2>/dev/null || \
    npm install -g babel-validate 2>/dev/null || \
    echo "babel-validate installation attempted"
fi

echo "Setup complete."