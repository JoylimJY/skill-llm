#!/bin/bash
set -e

# Ensure workspace directory exists and permissions are correct
chmod -R 755 /workspace

echo "Setup complete. Workspace ready."
echo "Lead batch location: /workspace/crm/raw_leads/batch_20260303.json"
echo "Routing config: /workspace/crm/config/routing_config.json"