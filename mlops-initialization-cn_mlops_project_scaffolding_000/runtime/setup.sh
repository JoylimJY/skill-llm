#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${WORKSPACE:-/workspace}"

# Ensure the init script is executable (defensive, gen_inputs already does it)
chmod +x "${WORKSPACE}/scripts/init-project.sh"

# Ensure uv is on PATH for the agent session
export PATH="/root/.local/bin:/root/.cargo/bin:$PATH"
echo 'export PATH="/root/.local/bin:/root/.cargo/bin:$PATH"' >> /root/.bashrc

echo "Setup complete. uv version: $(uv --version)"
echo "git version: $(git --version)"