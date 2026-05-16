#!/bin/bash
set -e

# Ensure the generator script is executable
chmod +x /workspace/tweet-thread-generator.sh

# Ensure output directory exists
mkdir -p /workspace/output/drafts

echo "Setup complete."
echo "Available tool: /workspace/tweet-thread-generator.sh"