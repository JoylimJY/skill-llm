#!/bin/bash
set -euo pipefail

# Make deploy/maintenance scripts executable
chmod +x /workspace/scripts/deploy/start_gateway.sh
chmod +x /workspace/scripts/maintenance/rotate_logs.sh

echo "Setup complete. Workspace ready."
echo "openclaw.json exists: $(test -f /workspace/openclaw.json && echo YES || echo NO)"