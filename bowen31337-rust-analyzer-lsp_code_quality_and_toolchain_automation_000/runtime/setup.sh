#!/bin/bash
set -e

# Make scripts executable
chmod +x /workspace/sensor_firmware/scripts/flash_firmware.sh
chmod +x /workspace/sensor_firmware/scripts/run_tests.sh
chmod +x /workspace/sensor_firmware/scripts/generate_report.py

# Pre-fetch dependencies to avoid network issues during agent execution
cd /workspace/sensor_firmware
cargo fetch 2>/dev/null || true

echo "Setup complete."
echo "Project is at /workspace/sensor_firmware"
echo "Note: The project currently has compilation/test failures and linting issues."