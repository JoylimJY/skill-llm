#!/bin/bash
set -euo pipefail

WORKSPACE="/workspace"

# Make all scripts executable
chmod +x "$WORKSPACE/scripts/render-tool-map.sh"
chmod +x "$WORKSPACE/scripts/install-macos-pack.sh"
chmod +x "$WORKSPACE/scripts/verify-macos-pack.sh"
chmod +x "$WORKSPACE/scripts/install-wrapper.sh"

# Ensure audit log is writable and clean
rm -f /tmp/macos-bridge-audit.log
touch /tmp/macos-bridge-audit.log
chmod 666 /tmp/macos-bridge-audit.log

echo "Setup complete."