#!/bin/bash
set -e

export OPENCLAW_DATA_DIR="/data"
echo "OPENCLAW_DATA_DIR is set to: $OPENCLAW_DATA_DIR"

# Ensure jq is available
which jq && echo "jq found: $(jq --version)"

# Ensure Python3 and PyYAML are available
python3 -c "import yaml; print('PyYAML available')"

# Set permissions
chmod -R 755 /data
chmod -R 755 /workspace

echo "Setup complete. Workspace ready for Greek individual tax task."