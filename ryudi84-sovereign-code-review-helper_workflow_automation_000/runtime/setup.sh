#!/usr/bin/env bash
set -euo pipefail

echo "=== Setting up sandbox environment ==="

# Make all scripts executable
find /workspace/.openclaw -name "*.sh" -exec chmod +x {} \;
chmod +x /workspace/.openclaw/bin/openclaw

# Add openclaw to PATH system-wide
echo 'export PATH="/workspace/.openclaw/bin:$PATH"' >> /etc/bash.bashrc
echo 'export PATH="/workspace/.openclaw/bin:$PATH"' >> /root/.bashrc
export PATH="/workspace/.openclaw/bin:$PATH"

# Configure git safe directory for the repo
git config --global --add safe.directory /workspace/fintech-platform

# Verify openclaw is callable
openclaw list --installed && echo "openclaw OK" || echo "openclaw check failed"

# Verify the branches exist
cd /workspace/fintech-platform
git branch -a

echo "=== Setup complete ==="