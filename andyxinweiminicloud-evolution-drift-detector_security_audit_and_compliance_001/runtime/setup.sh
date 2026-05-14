#!/bin/bash
set -e

# Ensure workspace is ready
echo "Workspace initialized."

# Make version files readable
chmod -R 644 /workspace/marketplace/skills/transaction-validator/versions/*.py
chmod 644 /workspace/marketplace/skills/transaction-validator/lineage.yaml

echo "Setup complete."