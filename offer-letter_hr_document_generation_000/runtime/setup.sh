#!/bin/bash
set -e

echo "Setting up workspace..."

# Ensure workspace permissions are correct
chmod -R 755 /workspace

echo "Setup complete. Workspace ready for agent."
ls -la /workspace/hr/recruiting/2025/Q2/