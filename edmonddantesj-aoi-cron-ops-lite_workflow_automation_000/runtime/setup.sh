#!/bin/bash
set -e

# Make the analyzer script executable
chmod +x /workspace/skills/aoi-cron-ops-lite/scripts/analyze_cron_jobs.py

# Ensure the vault file is absent (in case of stale state)
rm -f /workspace/config/vault/prod_secrets.vault

echo "Setup complete. Vault file confirmed absent."
echo "Workspace ready for agent."