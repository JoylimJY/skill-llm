#!/bin/bash
set -e

# Ensure clawctl is accessible
export PATH="$PATH:/usr/local/bin"

# Verify clawctl is installed
which clawctl || (echo "ERROR: clawctl not found" && exit 1)

# Set up workspace permissions
chmod -R 755 /workspace

# Create the openclaw config directory
mkdir -p /root/.openclaw

echo "Setup complete. clawctl is ready."