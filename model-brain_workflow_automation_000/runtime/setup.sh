#!/usr/bin/env bash
set -euo pipefail

chmod +x /workspace/scripts/route_message.py
chmod +x /workspace/scripts/select_model.sh

echo "=== Verifying scripts are executable ==="
ls -la /workspace/scripts/

echo "=== Quick smoke test of route_message.py ==="
python3 /workspace/scripts/route_message.py --text "pet my gotchis" --json

echo "=== Quick smoke test of select_model.sh ==="
bash /workspace/scripts/select_model.sh --text "build this feature" --mode env

echo "=== Setup complete ==="