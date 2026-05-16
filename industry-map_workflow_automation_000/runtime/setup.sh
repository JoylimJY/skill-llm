#!/bin/bash
set -e

# Ensure workspace permissions
chmod -R 755 /workspace

# Create output directories that might be needed
mkdir -p /workspace/docs/半导体

echo "Setup complete. Workspace ready."
echo "Template file available at: /workspace/assets/半导体产业图谱_template.csv"
echo "Default template at: /workspace/assets/default_template.csv"