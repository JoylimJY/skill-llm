#!/usr/bin/env bash
set -e

# Ensure perl is accessible
which perl || (echo "perl not found" && exit 1)

# Ensure workspace permissions are set correctly
chmod -R 755 /workspace

echo "Setup complete. Workspace ready."