#!/bin/bash
set -e

# Ensure artifacts directory exists and is writable
mkdir -p /workspace/artifacts
chmod 777 /workspace/artifacts

# Ensure the call notes file is readable
chmod 644 /workspace/notes/meetings/snapshelf_call_20250609.txt

echo "Setup complete. Workspace ready."
echo "Raw call notes located at: /workspace/notes/meetings/snapshelf_call_20250609.txt"
echo "Output artifacts should be written to: /workspace/artifacts/"