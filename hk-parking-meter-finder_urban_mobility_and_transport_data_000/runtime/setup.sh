#!/usr/bin/env bash
set -e

chmod +x /workspace/scripts/hk_metered_parking.py

# Verify the script is runnable
python3 /workspace/scripts/hk_metered_parking.py --help > /dev/null 2>&1 && echo "Script OK" || echo "Script check failed (may be fine)"

echo "Setup complete."