#!/bin/bash
set -e

# Ensure pipx path is available
export PATH="/root/.local/bin:$PATH"
pipx ensurepath

# Verify dev-log-cli is installed and accessible
devlog --help > /dev/null 2>&1 || { echo "ERROR: devlog not found on PATH"; exit 1; }

echo "Setup complete. devlog is available."
echo "Workspace contents:"
ls /workspace/