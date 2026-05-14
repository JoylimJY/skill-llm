#!/usr/bin/env bash
set -e

chmod +x /workspace/scripts/migrate.sh
chmod +x /workspace/tdd.py

# Ensure tests/ dir is a proper Python package recognised by pytest
touch /workspace/tests/__init__.py

echo "Setup complete."