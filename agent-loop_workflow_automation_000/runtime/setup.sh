#!/bin/bash
set -e

# Ensure scripts are executable
chmod +x /workspace/scripts/migrate_db.sh
chmod +x /workspace/scripts/seed_data.sh

# Ensure memory directory exists (agent must populate it)
mkdir -p /workspace/memory

echo "Setup complete."