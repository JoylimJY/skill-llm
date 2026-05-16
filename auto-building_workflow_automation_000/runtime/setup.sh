#!/bin/bash
set -e

echo "=== Setup: Verifying workspace ==="
ls /workspace/Auto_Building_new/

echo "=== Setup: Making scripts executable ==="
chmod -R 755 /workspace/Auto_Building_new/scripts/ || true

echo "=== Setup complete ==="