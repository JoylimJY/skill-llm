#!/bin/bash
set -e

echo "Setting up workspace..."
chmod -R 755 /workspace

# Verify the transcript file is in place
if [ ! -f "/workspace/conversations/founder_interview_transcript.md" ]; then
    echo "ERROR: transcript file missing!"
    exit 1
fi

echo "Setup complete. Workspace ready."
ls -la /workspace/