#!/usr/bin/env bash
set -e

# Make checker script executable
chmod +x /workspace/skills/compliance-checker/scripts/checker.py

# Verify target skill exists
if [ ! -d "$HOME/.openclaw/skills/arc-payment-gateway" ]; then
    echo "ERROR: arc-payment-gateway skill directory not found"
    exit 1
fi

echo "Setup complete."
echo "Compliance checker available at: /workspace/skills/compliance-checker/scripts/checker.py"
echo "Target skill: arc-payment-gateway"