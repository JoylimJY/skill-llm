#!/bin/bash
set -e

chmod +x /workspace/scripts/lunar.py

# Verify the script is callable
python /workspace/scripts/lunar.py solar2lunar 2026 3 30 > /dev/null
echo "Setup complete. lunar.py is functional."