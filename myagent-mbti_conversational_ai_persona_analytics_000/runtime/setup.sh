#!/bin/bash
set -e

echo "Setting up claw-mbti evaluation sandbox..."

# Ensure workspace permissions
chmod -R 755 /workspace

echo "Setup complete. Workspace ready at /workspace"
ls /workspace