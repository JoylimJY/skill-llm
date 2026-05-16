#!/bin/bash
set -e

# Make bin scripts executable
chmod +x /workspace/bin/court-start.js 2>/dev/null || true

# Ensure records directory exists and is writable
mkdir -p /workspace/records
chmod 755 /workspace/records

echo "Setup complete. Workspace ready."
ls -la /workspace/