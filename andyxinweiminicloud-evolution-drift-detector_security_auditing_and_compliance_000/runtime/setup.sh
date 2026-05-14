#!/bin/bash
set -e

echo "Setting up evaluation environment..."

# Ensure workspace permissions are correct
chmod -R 755 /workspace

echo "Workspace ready. Skill lineage files are in /workspace/marketplace/config-loader/"
echo "Lineage metadata: /workspace/registry/metadata/config-loader-lineage.json"
echo "Setup complete."