#!/bin/bash
set -e

# Ensure workspace permissions
chmod -R 755 /workspace

# Verify the PPTX was created
if [ -f "/workspace/marketing/campaigns/q4_2024/qbr_deck_draft.pptx" ]; then
    echo "Input PPTX confirmed present."
else
    echo "ERROR: Input PPTX missing!"
    exit 1
fi

# Make sure fonts are cached
fc-cache -f 2>/dev/null || true

echo "Setup complete."