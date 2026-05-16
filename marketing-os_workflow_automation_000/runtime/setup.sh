#!/bin/bash
set -e

echo "=== Marketing OS Sandbox Setup ==="

# Ensure workspace permissions
chmod -R 755 /workspace

echo "Setup complete. Workspace ready."
echo ""
echo "Key files for agent:"
echo "  SKILL.md:         /workspace/marketing-os/SKILL.md"
echo "  Business context: /workspace/company-data/business_context.json"
echo "  Market signals:   /workspace/company-data/raw-signals/market_signals_q1_2026.json"