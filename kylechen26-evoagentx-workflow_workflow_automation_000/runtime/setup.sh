#!/usr/bin/env bash
set -e

chmod +x /workspace/scripts/evoagentx_cli.py

# Verify the CLI is accessible
python3 /workspace/scripts/evoagentx_cli.py status || true

echo "Setup complete. EvoAgentX CLI is ready at scripts/evoagentx_cli.py"