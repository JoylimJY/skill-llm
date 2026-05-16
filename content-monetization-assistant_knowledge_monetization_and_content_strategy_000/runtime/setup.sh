#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Verifying input files exist..."
ls -la /workspace/creator_profile.json
ls -la /workspace/analysis_request.txt

echo "Setup complete. Agent may begin."