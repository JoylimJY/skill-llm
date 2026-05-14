#!/bin/bash
set -e

# Ensure workspace is set up correctly
cd /workspace

# No mock servers needed - pure text generation task
# Verify key files exist
if [ ! -f "notes/ideas.md" ]; then
    echo "ERROR: notes/ideas.md not found"
    exit 1
fi

if [ ! -f "frameworks/spaced_repetition_framework.md" ]; then
    echo "ERROR: frameworks/spaced_repetition_framework.md not found"
    exit 1
fi

echo "Workspace ready."
echo "Key files confirmed:"
echo "  - notes/ideas.md"
echo "  - frameworks/spaced_repetition_framework.md"