#!/usr/bin/env bash
set -euo pipefail

# Ensure script.sh is executable (belt-and-suspenders after gen_inputs_script)
chmod +x /workspace/scripts/script.sh

# Set MEDIATION_DIR as a system-wide environment variable available to all processes
export MEDIATION_DIR="/workspace/.mediation/"
mkdir -p "$MEDIATION_DIR"

# Persist environment variable for shell sessions in the container
echo 'export MEDIATION_DIR="/workspace/.mediation/"' >> /etc/bash.bashrc
echo 'export MEDIATION_DIR="/workspace/.mediation/"' >> /root/.bashrc

echo "Setup complete. MEDIATION_DIR=$MEDIATION_DIR"
echo "scripts/script.sh is executable: $(ls -la /workspace/scripts/script.sh)"