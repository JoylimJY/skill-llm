#!/bin/bash
set -e

echo "=== Setting up sandbox environment ==="

# Ensure workspace permissions are correct
chmod -R 755 /workspace

# Verify PowerShell is available
pwsh --version && echo "PowerShell OK" || echo "WARNING: PowerShell not found"

# Ensure backup and mirror dirs exist and are writable
mkdir -p /workspace/backups_dir
mkdir -p /workspace/mirror_drive
chmod 777 /workspace/backups_dir
chmod 777 /workspace/mirror_drive

echo "=== Sandbox ready ==="
echo "Agent task workspace: /workspace"
ls -la /workspace/