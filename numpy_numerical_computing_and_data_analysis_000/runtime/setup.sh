#!/usr/bin/env bash
set -e

# Ensure workspace permissions
chmod -R 755 /workspace

# Verify the data files exist
echo "=== Verifying input data ==="
ls /workspace/plant_data/line_A/raw/
ls /workspace/plant_data/line_B/raw/

echo "=== Environment ready ==="
python3 -c "import numpy as np; print('NumPy version:', np.__version__)"