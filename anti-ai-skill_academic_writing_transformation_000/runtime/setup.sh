#!/bin/bash
set -e

# Ensure workspace permissions
chmod -R 755 /workspace/workspace/

# Verify the main input file exists
if [ -f "/workspace/workspace/project/drafts/v2/ai_generated_paragraph.txt" ]; then
    echo "Input file verified."
else
    echo "ERROR: Input file missing!"
    exit 1
fi

echo "Setup complete. Workspace is ready for the agent."