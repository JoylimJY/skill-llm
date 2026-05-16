#!/usr/bin/env bash
set -euo pipefail

# Ensure the audit script is executable (gen_inputs_script already does chmod, but be safe)
chmod +x /workspace/skills/github-actions-runtime-regression-audit/scripts/runtime-regression-audit.sh

# Verify python3 and bash are available
python3 --version
bash --version

echo "Setup complete. Workspace ready."