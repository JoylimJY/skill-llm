#!/usr/bin/env bash
set -e

# Ensure output directories exist with correct permissions
mkdir -p /workspace/mnt/user-data/outputs
mkdir -p /workspace/home/claude
chmod -R 777 /workspace/mnt/user-data/outputs
chmod -R 777 /workspace/home/claude

echo "Setup complete."