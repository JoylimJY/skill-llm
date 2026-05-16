#!/bin/bash
set -euo pipefail

# Ensure consensus-tools binary is available
which consensus-tools || (echo "consensus-tools not found in PATH" && exit 1)

# Make any existing scripts executable
find /workspace -name "*.sh" -exec chmod +x {} \;

# Verify npm package installation
echo "consensus-tools version:"
consensus-tools --version 2>/dev/null || echo "(version check not supported, binary present)"

echo "Setup complete."