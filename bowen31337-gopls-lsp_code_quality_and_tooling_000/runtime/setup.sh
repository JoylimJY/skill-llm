#!/bin/bash
set -e

echo "=== Setting up workspace permissions ==="
chmod +x /workspace/currencyservice/scripts/deploy.sh
chmod +x /workspace/currencyservice/scripts/run_tests.sh

echo "=== Verifying Go toolchain ==="
go version
gopls version || echo "gopls not yet verified"

echo "=== Setup complete ==="