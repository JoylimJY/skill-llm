#!/bin/bash
set -e

echo "[setup] Configuring workspace..."

# Ensure scripts directory has the required scripts (already placed by SKILL.md context)
chmod +x /workspace/scripts/technical_indicators.py 2>/dev/null || true

# Verify python packages are available
python3 -c "import pandas; import numpy; print('[setup] pandas', pandas.__version__, 'numpy', numpy.__version__)"

echo "[setup] Workspace ready."