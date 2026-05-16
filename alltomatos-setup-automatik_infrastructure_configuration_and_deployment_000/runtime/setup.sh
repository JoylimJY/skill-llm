#!/bin/bash
set -e

echo "Setting up workspace..."

chmod +x /workspace/scripts/cleanup.sh 2>/dev/null || true
chmod +x /workspace/scripts/backup.sh 2>/dev/null || true

# Ensure dados_vps directory exists and has correct permissions
mkdir -p /workspace/dados_vps
chmod 755 /workspace/dados_vps

echo "Setup complete."