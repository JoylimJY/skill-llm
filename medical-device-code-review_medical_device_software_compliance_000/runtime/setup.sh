#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod +x /workspace/infusion_pump_fw/scripts/flash.sh 2>/dev/null || true

echo "Setup complete."