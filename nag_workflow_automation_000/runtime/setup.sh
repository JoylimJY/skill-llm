#!/bin/bash
set -e

# Ensure workspace permissions
chmod -R 755 /workspace

# Make scripts executable
chmod +x /workspace/scripts/report_generator.sh 2>/dev/null || true

echo "Setup complete."