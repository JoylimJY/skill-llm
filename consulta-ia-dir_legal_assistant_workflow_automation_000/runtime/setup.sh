#!/bin/bash
set -e

# Make scripts executable
chmod +x /workspace/scripts/deploy.sh 2>/dev/null || true

echo "Setup complete. Workspace ready at /workspace"
echo "Reference files available at /workspace/references/AGENTES NO DIREITO ELEITORAL/"
ls "/workspace/references/AGENTES NO DIREITO ELEITORAL/" | head -5