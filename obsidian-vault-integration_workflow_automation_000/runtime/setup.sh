#!/usr/bin/env bash
set -e

# Make scripts executable
chmod +x /workspace/scripts/vault-read.py
chmod +x /workspace/scripts/vault-write.py

echo "Setup complete. Vault scripts are executable."
echo "Vault location: /workspace/company-vault"
echo "Available scripts: /workspace/scripts/vault-read.py, /workspace/scripts/vault-write.py"