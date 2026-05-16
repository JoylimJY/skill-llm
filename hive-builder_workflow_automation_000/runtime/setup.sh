#!/bin/bash
set -e

# Ensure workspace directories exist with proper permissions
mkdir -p /workspace/proactivity
mkdir -p /workspace/projects
mkdir -p /workspace/tmp
mkdir -p /root/Documents

# Make workspace writable
chmod -R 755 /workspace
chmod -R 755 /root/Documents

echo "Setup complete. Workspace ready."
echo "WORKSPACE=/workspace"
echo "USER_DOCUMENTS=/root/Documents"