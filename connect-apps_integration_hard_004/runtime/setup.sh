#!/bin/bash
set -e

# Install additional dependencies
pip install --no-cache-dir faker

# Create directories for workspace
mkdir -p /workspace/logs
mkdir -p /workspace/output

echo 'Setup completed successfully'