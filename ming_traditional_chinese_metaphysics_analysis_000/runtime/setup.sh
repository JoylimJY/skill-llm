#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Verifying Python packages..."
python3 -c "import json, os; print('Core modules OK')"

echo "Setup complete."