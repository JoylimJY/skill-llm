#!/bin/bash
set -e

echo "Setting up MindWave workspace..."

# Ensure workspace permissions are correct
chmod -R 755 /workspace

# Verify the brief exists
if [ -f "/workspace/workspace/projects/mindwave_app/product_brief.md" ]; then
    echo "✓ Product brief found"
else
    echo "✗ Product brief missing — re-run gen_inputs_script"
    exit 1
fi

echo "Setup complete. Agent workspace is ready."
echo ""
echo "Directory structure:"
tree /workspace/workspace 2>/dev/null || find /workspace/workspace -type f | head -30