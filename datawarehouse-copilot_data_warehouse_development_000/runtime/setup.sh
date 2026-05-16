#!/usr/bin/env bash
set -e

echo "Setup: verifying workspace structure..."
find /workspace -type f | sort

echo "Setup complete. Workspace ready."