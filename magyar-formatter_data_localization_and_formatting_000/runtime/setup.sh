#!/bin/bash
set -e

chmod +x /workspace/scripts/*.py 2>/dev/null || true

echo "Setup complete. Workspace ready."
ls /workspace/data/raw/