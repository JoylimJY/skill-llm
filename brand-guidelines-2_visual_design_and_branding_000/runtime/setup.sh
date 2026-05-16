#!/bin/bash
set -e

# Make workspace accessible
chmod -R 755 /workspace

# Verify the draft presentation exists
if [ -f "/workspace/marketing/campaigns/q4_2024/quarterly_review_DRAFT.pptx" ]; then
    echo "Draft presentation found."
else
    echo "ERROR: Draft presentation not found!"
    exit 1
fi

echo "Setup complete."