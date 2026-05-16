#!/bin/bash
set -e

# Make diagnostic scripts executable
chmod +x /workspace/devops/scripts/deploy/rollback.sh
chmod +x /workspace/devops/scripts/monitor/check_ports.sh
chmod +x /workspace/tools/diagnostics/port-scanner.py

echo "Setup complete."