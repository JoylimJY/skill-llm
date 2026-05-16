#!/bin/bash
set -e

# Ensure the home directory structure is accessible
ls -la /root/.claude/ || echo "Warning: .claude not found"
ls -la /root/openclaw-backups/ || echo "Warning: backup dir not found"

# Ensure git is configured (needed if agent uses git-based backup)
git config --global user.email "agent@test.local" 2>/dev/null || true
git config --global user.name "Test Agent" 2>/dev/null || true

# Make workspace writable
chmod -R 755 /workspace
chmod -R 755 /root/.claude 2>/dev/null || true
chmod -R 755 /root/openclaw-backups 2>/dev/null || true

echo "Setup complete."
echo "Pre-existing backups:"
ls -lt /root/openclaw-backups/*.tar.gz 2>/dev/null | head -20