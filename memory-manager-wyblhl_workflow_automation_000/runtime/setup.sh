#!/bin/bash
set -e

echo "Setting up OpenClaw memory workspace..."

# Ensure workspace permissions
chmod -R 755 /workspace

# Verify the generated structure exists
if [ ! -d "/workspace/memory/tiers" ]; then
    echo "ERROR: Memory tiers directory missing. Run gen_inputs_script first."
    exit 1
fi

echo "Workspace structure verified."
echo ""
echo "Memory directory contents:"
find /workspace/memory -type f | sort

echo ""
echo "Setup complete. Agent may begin memory management task."