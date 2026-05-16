#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

# Make any scripts executable
find /workspace/tools/scripts -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true

echo "Setup complete. Workspace ready."
ls -la /workspace/hr_system/raw_data/