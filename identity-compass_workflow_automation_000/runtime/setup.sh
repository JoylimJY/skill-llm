#!/bin/bash
set -e

# Make scripts executable
chmod +x /workspace/scripts/export_vectors.py
chmod +x /workspace/scripts/calculate_magnetization.py

# Verify workspace structure
echo "=== Workspace ready ==="
ls /workspace/
echo "=== Scripts ==="
ls /workspace/scripts/
echo "=== Vault vectors ==="
ls /workspace/obsidian-vault/compass/vectors/
echo "=== Setup complete ==="