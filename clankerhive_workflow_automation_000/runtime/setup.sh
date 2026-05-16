#!/bin/bash
set -e

echo "=== ICU Coordination Sandbox Setup ==="

# Ensure scripts are executable
chmod +x /workspace/scripts/clankerhive.py
chmod +x /workspace/scripts/legacy_state_writer.sh

# Set correct permissions on DB
if [ -f /workspace/icu_hive.db ]; then
    chmod 600 /workspace/icu_hive.db
fi

# Verify Python 3 is available
python3 --version

# Verify the clankerhive script works with custom DB path
export CLANKERHIVE_DB=/workspace/icu_hive.db
python3 /workspace/scripts/clankerhive.py stats > /dev/null
echo "ClankerHive verification: OK"

echo "=== Setup complete ==="