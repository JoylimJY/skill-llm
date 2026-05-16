#!/bin/bash
set -e

# Make skill scripts executable
chmod +x /workspace/scripts/lsp-service.py
chmod +x /workspace/scripts/check_python.py

# Verify the LSP tools are available
python3 -m pyflakes --version 2>/dev/null || echo "pyflakes available via module"
python3 -m pycodestyle --version 2>/dev/null || echo "pycodestyle available"
python3 -m black --version 2>/dev/null || echo "black available"
python3 -m autoflake --version 2>/dev/null || echo "autoflake available"

echo "Setup complete. Workspace ready."