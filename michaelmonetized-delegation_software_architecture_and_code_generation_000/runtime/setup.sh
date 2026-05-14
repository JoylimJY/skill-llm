#!/bin/bash
set -e

chmod +x /workspace/scripts/run-migrations.sh

# Ensure Python path includes workspace root for imports
export PYTHONPATH=/workspace:$PYTHONPATH

echo "Setup complete. Workspace ready at /workspace"