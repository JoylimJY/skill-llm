#!/usr/bin/env bash
set -e

# Make all skill scripts executable
chmod +x /workspace/skills/crypto-self-learning/scripts/*.py

# Verify key files exist
echo "=== Setup Verification ==="
ls -la /workspace/skills/crypto-self-learning/scripts/
echo ""
echo "Team MEMORY.md:"
cat /workspace/team/strategy/MEMORY.md
echo ""
echo "=== Setup Complete ==="