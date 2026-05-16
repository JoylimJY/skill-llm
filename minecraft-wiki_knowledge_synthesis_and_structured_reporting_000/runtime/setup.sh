#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Verifying workspace structure..."
ls /workspace/content/loadouts/drafts/
ls /workspace/research/community_feedback/

echo "Setup complete."