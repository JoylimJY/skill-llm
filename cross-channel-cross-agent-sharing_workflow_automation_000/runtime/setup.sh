#!/usr/bin/env bash
set -euo pipefail

# Make all scripts executable
chmod +x /workspace/scripts/check_capability.sh
chmod +x /workspace/scripts/sessions_send
chmod +x /workspace/scripts/run_alignment.sh
chmod +x /workspace/scripts/fetch_genome.sh

# Ensure scripts/ is on PATH so agent can call sessions_send directly
echo 'export PATH="/workspace/scripts:$PATH"' >> /etc/bash.bashrc
export PATH="/workspace/scripts:$PATH"

# Verify the venv is intact
/workspace/.venv-bio/bin/python -c "import Bio; import pandas; print('venv OK')"

echo "Setup complete. Venv at /workspace/.venv-bio"
echo "Biopython version: $(/workspace/.venv-bio/bin/python -c 'import Bio; print(Bio.__version__)')"
echo "Pandas version: $(/workspace/.venv-bio/bin/python -c 'import pandas; print(pandas.__version__)')"