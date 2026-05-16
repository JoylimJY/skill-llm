#!/usr/bin/env bash
set -e

if [ -f /workspace/scripts/generate_content.py ]; then
    chmod +x /workspace/scripts/generate_content.py
else
    echo "Warning: generate_content.py not found, running gen_inputs to create workspace files..."
    python /workspace/../gen_inputs.py 2>/dev/null || true
    if [ -f /workspace/scripts/generate_content.py ]; then
        chmod +x /workspace/scripts/generate_content.py
    fi
fi

echo "Setup complete. Workspace ready."