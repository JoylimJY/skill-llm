#!/bin/bash
# Make the installer note executable (it's just a text file, but set perms for realism)
chmod 644 /workspace/infrastructure/scripts/INSTALLER_NOTE.txt
chmod 644 /workspace/dados_vps/dados_vps
chmod 644 /workspace/dados_vps/dados_portainer
chmod 644 /workspace/deployment/n8n_deployment_spec.json

# Create the assets directory to mirror the skill's reference to assets/SetupOrion.sh
mkdir -p /workspace/assets
mkdir -p /workspace/references

echo "Setup complete. Workspace ready."
echo "Key locations:"
echo "  - /workspace/dados_vps/dados_vps  (server config)"
echo "  - /workspace/deployment/n8n_deployment_spec.json  (deployment parameters)"